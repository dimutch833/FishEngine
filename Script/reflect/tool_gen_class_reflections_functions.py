from mako.template import Template
import json
from tool_helper import UpdateFile
from collections import OrderedDict
import os


serialization_template_str = '''
/**************************************************
* auto generated by reflection system
**************************************************/

#include <Archive.hpp>
#include <private/CloneUtility.hpp>
% for h in headers:
#include "${h}" 
% endfor

namespace ${scope}
{
% for c in ClassInfo:
<% T = c['ClassName'] %>
% if c['isPolymorphic']:
	// ${T}
	void ${T}::Serialize ( FishEngine::OutputArchive & archive ) const
	{
		//archive.BeginClass();
	% if 'parent' in c and T != 'FishEditor::AssetImporter':
		${c['parent']}::Serialize(archive);
	% endif
	% for member in c['members']:
		archive << FishEngine::make_nvp("${member['name']}", ${member['name']}); // ${member['type']}
	% endfor
		//archive.EndClass();
	}

	void ${T}::Deserialize ( FishEngine::InputArchive & archive )
	{
		//archive.BeginClass(2);
	% if 'parent' in c and T != 'FishEditor::AssetImporter':
		${c['parent']}::Deserialize(archive);
	% endif
	% for member in c['members']:
		archive >> FishEngine::make_nvp("${member['name']}", ${member['name']}); // ${member['type']}
	% endfor
		//archive.EndClass();
	}

	%if c['isComponent'] and T != 'FishEngine::Transform':
	FishEngine::ComponentPtr ${T}::Clone(FishEngine::CloneUtility & cloneUtility) const
	{
		% if T in ( 'FishEngine::Renderer', 'FishEngine::Collider', 'FishEngine::Transform'):
		abort();
		return nullptr;
		% else:
		auto ret = FishEngine::MakeShared<${T}>();
		cloneUtility.m_clonedObject[this->GetInstanceID()] = ret;
		this->CopyValueTo(ret, cloneUtility);
		return ret;
		% endif
	}

	void ${T}::CopyValueTo(std::shared_ptr<${T}> target, FishEngine::CloneUtility & cloneUtility) const
	{
		% if 'parent' in c:
		${c['parent']}::CopyValueTo(target, cloneUtility);
		% endif
		% for member in c['members']:
		cloneUtility.Clone(this->${member['name']}, target->${member['name']}); // ${member['type']}
		% endfor
	}
	%endif

% else:
	// ${T}
	FishEngine::OutputArchive & operator << ( FishEngine::OutputArchive & archive, ${T} const & value )
	{
		archive.BeginClass();
	% for member in c['members']:
		archive << FishEngine::make_nvp("${member['name']}", value.${member['name']}); // ${member['type']}
	% endfor
		archive.EndClass();
		return archive;
	}

	FishEngine::InputArchive & operator >> ( FishEngine::InputArchive & archive, ${T} & value )
	{
		archive.BeginClass();
	% for member in c['members']:
		archive >> FishEngine::make_nvp("${member['name']}", value.${member['name']}); // ${member['type']}
	% endfor
		archive.EndClass();
		return archive;
	}
% endif
% endfor

} // namespace ${scope}
'''
serialization_template = Template(serialization_template_str)

blacklist = ("FishEngine::Vector2",
	"FishEngine::Vector3",
	"FishEngine::Vector4",
	"FishEngine::Matrix4x4",
	"FishEngine::Quaternion");


def GenSerializationFunctions(classinfo, scope, root_dir):
	def IsObject(name):
		if name == "FishEngine::Object":
			return True
		if 'parent' not in class_info[name]:
			return False
		return IsObject(class_info[name]['parent'])

	def IsComponent(name):
		if name == "FishEngine::Component":
			return True
		if 'parent' not in class_info[name]:
			return False
		return IsComponent(class_info[name]['parent'])

	headers = []
	ClassInfo = []

	for key in classinfo.keys():
		#register(key)
		if key in blacklist:
			continue
		c = {}
		c['ClassName'] = key
		item = classinfo[key]
		header_path = item['header_file']
		header_path = os.path.relpath(header_path, root_dir)
		header_path = header_path.replace('\\', '/')
		headers.append(header_path)
		if IsObject(key):
			c['isPolymorphic'] = True
		else:
			c['isPolymorphic'] = False
		c['members'] = [m for m in item['members'] if not m['NonSerializable']]
		if 'parent' in item:
			c['parent'] = item['parent']
		c['isComponent'] = IsComponent(key)
		ClassInfo.append(c)

	headers = set(headers)
	return serialization_template.render(headers = headers, scope = scope, ClassInfo=ClassInfo)


objectInheritance_template_str = '''
static std::map<int, int> s_objectInheritance =
{
	${pairs}
};
'''

def GenObjectInheritance(class_info):
	def IsObject(name):
		if name == "FishEngine::Object":
			return True
		if 'parent' not in class_info[name]:
			return False
		return IsObject(class_info[name]['parent'])

	pairs = []
	for key in class_info.keys():
		if "FishEngine::Object" == key:
			 pairs.append((key, ''))
		elif IsObject(key):
			pairs.append((key, class_info[key]['parent']))
	pairs = ['{{ClassID<{0}>(), ClassID<{1}>()}},'.format(x, y) for (x, y) in pairs]
	#print(pairs)
	print(Template(objectInheritance_template_str).render(pairs='\n\t'.join(pairs)))

DynamicSerializeObject_template_str = '''
namespace ${scope}
{
	template<class Archive>
	static void DynamicSerializeObject(Archive & archive, std::shared_ptr<FishEngine::Object> obj)
	{
		const int id = obj->ClassID();
		switch (id)
		{
		${dynamic_seqs};
		default:
			abort();
		}
	}
} // end of namespace ${scope}
'''

DynamicSerializeObject_seq = '''
		case FishEngine::ClassID<{0}>():
			archive << *std::dynamic_pointer_cast<{0}>(obj);
			break;'''

def Gen_DynamicSerializeObject(class_info, scope):
	def IsObject(name):
		if name == "FishEngine::Object":
			return True
		if 'parent' not in class_info[name]:
			return False
		return IsObject(class_info[name]['parent'])

	Objects = [ key for key in classinfo.keys() if key != "FishEngine::Object" and IsObject(key) ]
	seqs = ''.join([DynamicSerializeObject_seq.format(x) for x in Objects])
	return Template(DynamicSerializeObject_template_str).render(dynamic_seqs = seqs, scope = scope)


def GenSerialization(class_info, scope_prefix, root_dir):
	filtered_class_info = {k: v for k, v in class_info.iteritems() if v['scope_prefix'].startswith(scope_prefix)}
	return GenSerializationFunctions(filtered_class_info, scope_prefix, root_dir)

def GenSerialization_Engine(class_info):
	return GenSerialization(class_info, "FishEngine", "../../Engine/Source/Runtime/generate")

def GenSerialization_Editor(class_info):
	return GenSerialization(class_info, "FishEditor", "../../Engine/Source/Editor/generate")

if __name__ == "__main__":
	with open('temp/class.json') as f:
		class_info = json.loads(f.read())
		class_info = OrderedDict(sorted(class_info.items()))
	#GenObjectInheritance(class_info)
	UpdateFile('../../Engine/Source/Runtime/generate/EngineClassSerialization.cpp', GenSerialization_Engine(class_info))
	UpdateFile('../../Engine/Source/Editor/generate/EditorClassSerialization.cpp', GenSerialization_Editor(class_info))
	

