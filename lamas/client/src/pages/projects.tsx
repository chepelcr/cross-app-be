import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, ExternalLink, Laptop, Github, Bot } from "lucide-react";
import { useLanguage } from "@/contexts/language-context";

const getMainProjects = (t: any, language: string) => [
  {
    title: t("projects.beautyMarketTitle"),
    description: t("projects.beautyMarketDesc"),
    image: "/attached_assets/image_1754274082825.png",
    technologies: ["React", "TypeScript", "Node.js", "AWS Lambda", "PostgreSQL", "Cognito", "CloudFormation"],
    type: "SaaS Platform",
    features: [
      t("projects.beautyMarketFeature1"),
      t("projects.beautyMarketFeature2"),
      t("projects.beautyMarketFeature3"),
      t("projects.beautyMarketFeature4"),
    ],
    githubUrl: "https://github.com/chepelcr/BeautyMarket",
    liveUrl: "https://jmarkets.jcampos.dev",
  },
  {
    title: t("projects.videoTranscriptTitle"),
    description: t("projects.videoTranscriptDesc"),
    image: "/attached_assets/image_1754321230597.png", 
    technologies: ["React", "TypeScript", "AI Services", "Web APIs"],
    features: [
      t("projects.videoTranscriptFeature1"),
      t("projects.videoTranscriptFeature2"),
      t("projects.videoTranscriptFeature3"),
      t("projects.videoTranscriptFeature4"),
    ],
    liveUrl: language === 'es' ? "/video-transcript/es" : "/video-transcript/en",
  },
  {
    title: t("projects.linuxTitle"),
    description: t("projects.linuxDesc"),
    image: "/attached_assets/image_1754281123699.png",
    technologies: ["React", "TypeScript", "Tailwind CSS", "Node.js"],
    features: [
      t("projects.feature1"),
      t("projects.feature2"),
      t("projects.feature3"),
      t("projects.feature4"),
    ],
    liveUrl: "https://jcampos.dev/Comandos-linux/",
  },
];

const getOtherProjects = (t: any) => [
  {
    title: t("projects.erpTitle"),
    description: t("projects.erpDesc"),
    icon: Bot,
    erpUrl: "https://biller.jcampos.dev",
  },
];

export default function ProjectsPage() {
  const { t, language, navigateToSection } = useLanguage();
  const mainProjects = getMainProjects(t, language);
  const otherProjects = getOtherProjects(t);
  
  return (
    <div className="min-h-screen bg-slate pt-32">
      <div className="container-spacing">
        {/* Header */}
        <div className="flex items-center mb-12">
          <Button 
            variant="ghost" 
            className="mr-4"
            onClick={() => navigateToSection("home")}
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            {t("common.back")}
          </Button>
          <h1 className="text-3xl lg:text-4xl font-bold">
            <Laptop className="inline-block text-accent mr-4" />
            {t("projects.title")}
          </h1>
        </div>
        
        {/* Beauty Market SaaS - Full Width Row */}
        <div className="mb-12">
          <Card className="bg-card border-border card-hover h-full">
            <CardContent className="p-8 h-full flex flex-col lg:flex-row gap-8">
              <div className="lg:w-1/3">
                <img
                  src={mainProjects[0].image}
                  alt={mainProjects[0].title}
                  className="rounded-lg w-full h-48 lg:h-full object-cover"
                />
              </div>
              <div className="lg:w-2/3 flex flex-col">
                <h3 className="text-2xl font-semibold mb-4 text-accent">
                  {mainProjects[0].title}
                </h3>
                <p className="text-muted-foreground leading-relaxed mb-6">
                  {mainProjects[0].description}
                </p>
                
                {mainProjects[0].features && (
                  <div className="mb-6">
                    <h4 className="font-semibold mb-3">{t("projects.characteristics")}</h4>
                    <ul className="text-muted-foreground space-y-2">
                      {mainProjects[0].features.map((feature, featureIndex) => (
                        <li key={featureIndex} className="flex items-center">
                          <span className="text-accent mr-2">✓</span>
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                <div className="mb-6 flex-grow">
                  <h4 className="font-semibold mb-3">{t("projects.technologiesUsed")}</h4>
                  <div className="flex flex-wrap gap-2">
                    {mainProjects[0].technologies.map((tech, techIndex) => (
                      <Badge key={techIndex} className="bg-accent text-accent-foreground">
                        {tech}
                      </Badge>
                    ))}
                  </div>
                </div>
                
                <div className="flex flex-col sm:flex-row gap-4 mt-auto">
                  {mainProjects[0].liveUrl && (
                    <Button 
                      className="bg-accent text-accent-foreground hover:bg-accent/90"
                      onClick={() => window.open(mainProjects[0].liveUrl, "_blank")}
                    >
                      <ExternalLink className="mr-2 h-4 w-4" />
                      {t("projects.visitSite")}
                    </Button>
                  )}
                  {mainProjects[0].githubUrl && (
                    <Button 
                      variant="outline"
                      onClick={() => window.open(mainProjects[0].githubUrl, "_blank")}
                    >
                      <Github className="mr-2 h-4 w-4" />
                      {t("projects.viewCode")}
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Video Transcription and Linux Commands - Two Column Row */}        
        <div className="grid md:grid-cols-2 gap-8 mb-16">
          {mainProjects.slice(1).map((project, index) => (
            <Card key={index + 1} className="bg-card border-border card-hover h-full">
              <CardContent className="p-8 h-full flex flex-col">
                <div className="mb-6">
                  <img
                    src={project.image}
                    alt={project.title}
                    className="rounded-lg w-full h-48 object-cover"
                  />
                </div>
                <h3 className="text-2xl font-semibold mb-4 text-accent">
                  {project.title}
                </h3>
                <p className="text-muted-foreground leading-relaxed mb-6">
                  {project.description}
                </p>
                
                {project.features && (
                  <div className="mb-6">
                    <h4 className="font-semibold mb-3">{t("projects.characteristics")}</h4>
                    <ul className="text-muted-foreground space-y-2">
                      {project.features.map((feature, featureIndex) => (
                        <li key={featureIndex} className="flex items-center">
                          <span className="text-accent mr-2">✓</span>
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                <div className="mb-6 flex-grow">
                  <h4 className="font-semibold mb-3">
                    {project.features ? t("projects.technologies") : t("projects.technologiesUsed")}
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {project.technologies.map((tech, techIndex) => (
                      <Badge key={techIndex} className="bg-accent text-accent-foreground">
                        {tech}
                      </Badge>
                    ))}
                  </div>
                </div>
                
                <div className="flex flex-col sm:flex-row gap-4 mt-auto">
                  {project.liveUrl && (
                    <Button 
                      className="bg-accent text-accent-foreground hover:bg-accent/90"
                      onClick={() => window.open(project.liveUrl, "_blank")}
                    >
                      <ExternalLink className="mr-2 h-4 w-4" />
                      {t("projects.visitSite")}
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Additional Projects Preview */}
        <div className="text-center">
          <h3 className="text-xl font-semibold mb-8 text-accent">{t("projects.otherProjects")}</h3>
          <div className="grid md:grid-cols-1 gap-6 max-w-md mx-auto">
            {otherProjects.map((project, index) => (
              <Card key={index} className="bg-card border-border card-hover cursor-pointer" onClick={() => project.erpUrl && window.open(project.erpUrl, "_blank")}>
                <CardContent className="p-6 text-center">
                  <project.icon className="h-12 w-12 text-accent mx-auto mb-4" />
                  <h4 className="font-semibold mb-2">{project.title}</h4>
                  <p className="text-muted-foreground text-sm mb-4">{project.description}</p>
                  {project.erpUrl && (
                    <Button 
                      size="sm"
                      className="bg-accent text-accent-foreground hover:bg-accent/90"
                      onClick={(e) => {
                        e.stopPropagation();
                        window.open(project.erpUrl, "_blank");
                      }}
                    >
                      <ExternalLink className="mr-2 h-4 w-4" />
                      {t("projects.enterERP")}
                    </Button>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}