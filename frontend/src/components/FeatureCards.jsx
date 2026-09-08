import {
  Globe,
  Play,
  FileText,
  Database,
  Image
} from "lucide-react";


function FeatureCards({ onFeatureSelect }) {

  const features = [
    {
      id: "web",
      icon: Globe,
      title: "Search web",
      description: "Find current information"
    },
    {
      id: "youtube",
      icon: Play,
      title: "Find YouTube videos",
      description: "Search videos and transcripts"
    },
    {
      id: "pdf",
      icon: FileText,
      title: "Ask your PDFs",
      description: "Read and understand documents"
    },
    {
      id: "sql",
      icon: Database,
      title: "Query your data",
      description: "Ask questions about your data"
    },
    {
      id: "ocr",
      icon: Image,
      title: "Read images",
      description: "Extract and understand text"
    }
  ];


  return (
    <div className="feature-grid">

      {features.map((feature) => {

        const Icon = feature.icon;

        return (
          <button
            key={feature.id}
            className="feature-card"
            onClick={() =>
              onFeatureSelect?.(feature.id)
            }
          >

            <div className="feature-icon">

              <Icon
                size={20}
                strokeWidth={1.7}
              />

            </div>


            <div className="feature-content">

              <div className="feature-title">
                {feature.title}
              </div>

              <div className="feature-description">
                {feature.description}
              </div>

            </div>

          </button>
        );

      })}

    </div>
  );
}


export default FeatureCards;