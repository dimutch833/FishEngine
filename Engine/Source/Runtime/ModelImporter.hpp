#ifndef ModelImporter_hpp
#define ModelImporter_hpp

#include "AssetImporter.hpp"
#include "Mesh.hpp"
#include "GameObject.hpp"
#include "Scene.hpp"
#include "Material.hpp"
#include "MeshFilter.hpp"
#include "Animator.hpp"

struct aiNode;
struct aiMesh;
struct aiAnimation;

namespace FishEngine {

    struct ModelNode
    {
        uint32_t                index;
        std::string             name;
        ModelNode*              parent;
        std::vector<std::shared_ptr<ModelNode>> children;
        std::vector<uint32_t>   meshesIndices;
        //uint32_t                materialIndices;
        Matrix4x4               transform;
        bool                    isBone;
    };

    typedef std::shared_ptr<ModelNode> ModelNodePtr;
    

    class FE_EXPORT Meta(NonSerializable) Model
    {
    public:
        //InjectClassName(Model)

        Model() : m_avatar(std::make_shared<Avatar>()) {}
		
		Model(const Model&) = delete;
		Model& operator=(const Model& model) = delete;
        
        GameObjectPtr CreateGameObject() const;
        
        MeshPtr mainMesh() const
        {
            return m_meshes[0];
        }
        
        AnimationPtr mainAnimation() const
        {
            if (m_animations.empty())
                return nullptr;
            return m_animations.front();
        }

        AvatarPtr avatar() const
        {
            return m_avatar;
        }
        
        static void Init();
        
        static ModelPtr builtinModel(const PrimitiveType type);
        static MeshPtr builtinMesh(const PrimitiveType type);
        
    private:
        friend class ModelImporter;
		std::string m_name;

        void AddMesh(MeshPtr& mesh);

        GameObjectPtr
        ResursivelyCreateGameObject(const ModelNodePtr& node,
                                    std::map<std::string, std::weak_ptr<GameObject>>& nameToGameObject) const;
        
        std::vector<MaterialPtr> m_materials;
        std::vector<uint32_t> m_meterailIndexForEachMesh; // same size as m_meshes;
        std::vector<MeshPtr> m_meshes;

		Meta(NonSerializable)
        std::vector<AnimationPtr> m_animations;
        //std::vector<ModelNode::PModelNode> m_modelNodes;

		Meta(NonSerializable)
        ModelNodePtr m_rootNode;
        //std::vector<ModelNode::PModelNode> m_bones;
        //std::map<std::string, int> m_boneToIndex;
        AvatarPtr m_avatar;

        mutable std::weak_ptr<GameObject>   m_rootGameObject; // temp
        //mutable std::vector<std::weak_ptr<SkinnedMeshRenderer>> m_skinnedMeshRenderersToFindLCA;
        
        static std::map<PrimitiveType, ModelPtr> s_builtinModels;
        static std::map<PrimitiveType, MeshPtr> s_builtinMeshes;
    };

    // Vertex normal generation options for ModelImporter.
    enum class ModelImporterNormals
    {
        Import,     // Import vertex normals from model file(default).
        Calculate,  // Calculate vertex normals.
        None,       // Do not import vertex normals.
    };


    // Vertex tangent generation options for ModelImporter.
    enum class ModelImporterTangents
    {
        Import,         // Import vertex tangents from model file.
        //CalculateMikk,// Calculate tangents using MikkTSpace(default).
        Calculate,      // Calculate tangents.
        None,           // Do not import vertex tangents.
    };
    
    // Material naming options for ModelImporter.
    enum class ModelImporterMaterialName
    {
        BasedOnTextureName,                 // Use material names in the form <textureName>.mat.
        BasedOnMaterialName,                // Use a material name of the form <materialName>.mat.
        BasedOnModelNameAndMaterialName,    // Use material names in the form <modelFileName>-<materialName>.mat.
    };
    
    enum class ModelImporterAnimationType
    {
        None,       // Generate no animation data.
        //Legacy,     // Generate a legacy animation type.
        Generic,    // Generate a generic animator.
        Human,      // Generate a human animator.
    };
    
    enum class ModelImporterMaterialSearch
    {
        Local,          // Search in local Materials folder.
        RecursiveUp,    // Recursive-up search in Materials folders.
        Everywhere,     // Search in all project.
    };
    
    enum class ModelImporterMeshCompression
    {
        Off,        // No mesh compression (default).
        Low,        // Low amount of mesh compression.
        Medium,     // Medium amount of mesh compression.
        High,       // High amount of mesh compression.
    };
    
    enum class ModelImporterAnimationCompression
    {
        Off,                                // No animation compression.
        KeyframeReduction,                  // Perform keyframe reduction.
        KeyframeReductionAndCompression,    // Perform keyframe reduction and compression.
        Optimal,                            //Perform keyframe reduction and choose the best animation curve representation at runtime to reduce memory footprint (default).
    };
    
    class ModelImporter : public AssetImporter
    {
    public:
		InjectClassName(ModelImporter)

        ModelImporter() = default;
		
        void
        setFileScale(
            const float fileScale)
        {
            m_fileScale = fileScale;
        }
        
        ModelPtr LoadFromFile( const Path& path );

        void
        setImportNormals(
            ModelImporterNormals importNormals) 
        {
            m_importNormals = importNormals;
        }

        void
        setImportTangents(
            ModelImporterTangents importTangents) 
        {
            m_importTangents = importTangents;
        }

    private:
        
        float m_fileScale = 1.0f;
        
        ModelNodePtr
        buildModelTree(
            const aiNode*   assimp_node);
        
        MeshPtr
        ParseMesh(
            const aiMesh*   assimp_mesh,
            bool            load_uv,
            bool            load_tangent);

        void RemoveDummyNodeFBX( AnimationPtr animation );

		Meta(NonSerializable)
        ModelPtr      m_model;

        //VertexUsages m_vertexUsages = (int)VertexUsage::PNUT;

        // Vertex normal import options.
        ModelImporterNormals m_importNormals    = ModelImporterNormals::Import;

        // Vertex tangent import options.
        ModelImporterTangents m_importTangents  = ModelImporterTangents::Calculate;
        
        // Existing material search setting.
        ModelImporterMaterialSearch m_materialSearch;


        // remove dummy nodes
		Meta(NonSerializable)
        std::map<std::string, std::map<std::string, Matrix4x4>> m_nodeTransformations;
    };
}

#endif /* ModelImporter_hpp */
