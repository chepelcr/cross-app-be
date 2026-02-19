import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useLanguage } from "@/contexts/language-context";
import { 
  Code, 
  Cloud, 
  Database, 
  Settings, 
  Brain, 
  Users, 
  RotateCcw, 
  Rocket 
} from "lucide-react";

const getCoreSkills = (t: any) => [
  { name: "Java (Spring Boot)", level: t("skills.expert"), icon: "☕" },
  { name: "Python", level: t("skills.advanced"), icon: "🐍" },
  { name: "PHP", level: t("skills.intermediate"), icon: "🔧" },
  { name: "JavaScript & HTML", level: t("skills.intermediate"), icon: "🌐" },
];

const getCloudSkills = (t: any) => [
  { name: "AWS Infrastructure", level: t("skills.certified"), icon: "☁️" },
  { name: "Microservices Architecture", level: t("skills.expert"), icon: "🏗️" },
  { name: "Serverless Programming", level: t("skills.advanced"), icon: "⚡" },
  { name: "Docker & Container", level: t("skills.advanced"), icon: "🐳" },
];

const getDatabaseSkills = (t: any) => [
  { name: "MySQL", level: t("skills.advanced"), icon: "🗄️" },
  { name: "PostgreSQL", level: t("skills.advanced"), icon: "🐘" },
  { name: "Oracle", level: t("skills.basic"), icon: "🔶" },
  { name: "Microsoft SQL Server", level: t("skills.basic"), icon: "🗃️" },
];

const getToolsSkills = (t: any) => [
  { name: "Rest API Services", level: t("skills.expert"), icon: "🔗" },
  { name: "Linux", level: t("skills.advanced"), icon: "🐧" },
  { name: "Kafka", level: t("skills.intermediate"), icon: "📊" },
  { name: "Redis", level: t("skills.intermediate"), icon: "⚡" },
];

const getSoftSkills = (t: any) => [
  {
    icon: Brain,
    title: t("skills.analyticalThinking"),
    description: t("skills.analyticalDesc"),
  },
  {
    icon: Users,
    title: t("skills.teamwork"),
    description: t("skills.teamworkDesc"),
  },
  {
    icon: RotateCcw,
    title: t("skills.adaptability"),
    description: t("skills.adaptabilityDesc"),
  },
  {
    icon: Rocket,
    title: t("skills.initiative"),
    description: t("skills.initiativeDesc"),
  },
];

function SkillCard({ title, skills, icon: Icon }: { title: string; skills: any[]; icon: any }) {
  return (
    <Card className="bg-card border-border card-hover">
      <CardContent className="p-6">
        <h3 className="text-xl font-semibold mb-6 text-accent flex items-center">
          <Icon className="mr-3" />
          {title}
        </h3>
        <div className="space-y-4">
          {skills.map((skill, index) => (
            <div
              key={index}
              className="flex items-center justify-between bg-slate p-4 rounded-lg hover:bg-slate/80 transition-colors"
            >
              <span className="font-semibold flex items-center">
                <span className="mr-2">{skill.icon}</span>
                {skill.name}
              </span>
              <Badge className="bg-accent text-accent-foreground">
                {skill.level}
              </Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default function SkillsSection() {
  const { t } = useLanguage();
  const coreSkills = getCoreSkills(t);
  const cloudSkills = getCloudSkills(t);
  const databaseSkills = getDatabaseSkills(t);
  const toolsSkills = getToolsSkills(t);
  const softSkills = getSoftSkills(t);
  
  return (
    <section id="skills" className="section-spacing bg-navy">
      <div className="container-spacing">
        <h2 className="text-3xl lg:text-4xl font-bold text-center mb-16">
          <Code className="inline-block text-accent mr-4" />
          {t("skills.title")}
        </h2>
        
        <div className="grid lg:grid-cols-2 gap-8 mb-12">
          <SkillCard title={t("skills.backend")} skills={coreSkills} icon={Code} />
          <SkillCard title={t("skills.cloud")} skills={cloudSkills} icon={Cloud} />
          <SkillCard title={t("skills.databases")} skills={databaseSkills} icon={Database} />
          <SkillCard title={t("skills.tools")} skills={toolsSkills} icon={Settings} />
        </div>

        {/* Soft Skills */}
        <Card className="bg-card border-border card-hover">
          <CardContent className="p-8">
            <h3 className="text-2xl font-semibold mb-8 text-accent text-center">
              <Brain className="inline-block mr-3" />
              {t("skills.softSkills")}
            </h3>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              {softSkills.map((skill, index) => (
                <div key={index} className="text-center">
                  <div className="bg-accent text-accent-foreground w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3">
                    <skill.icon className="h-8 w-8" />
                  </div>
                  <h4 className="font-semibold mb-2">{skill.title}</h4>
                  <p className="text-muted-foreground text-sm">{skill.description}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}