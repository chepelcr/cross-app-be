import { Card, CardContent } from "@/components/ui/card";
import { User, Briefcase, Heart, Phone, Mail, MapPin, Globe } from "lucide-react";
import { useLanguage } from "@/contexts/language-context";

export default function AboutSection() {
  const { t } = useLanguage();
  return (
    <section id="about" className="section-spacing bg-slate">
      <div className="container-spacing">
        <h2 className="text-3xl lg:text-4xl font-bold text-center mb-16">
          <User className="inline-block text-accent mr-4" />
          {t("about.title")}
        </h2>
        <div className="grid lg:grid-cols-2 gap-12">
          <div>
            <Card className="bg-card border-border card-hover h-full">
              <CardContent className="p-6 h-full flex flex-col">
                <h3 className="text-xl font-semibold mb-4 text-accent flex items-center">
                  <Briefcase className="mr-2" />
                  {t("about.professionalProfile")}
                </h3>
                <div className="flex-grow">
                  <p className="text-muted-foreground leading-relaxed mb-4 text-justify">
                    {t("about.profileDesc1")}
                  </p>
                    <p className="text-muted-foreground leading-relaxed mb-4 text-justify">
                    {t("about.profileDesc3")}
                  </p>
                  <p className="text-muted-foreground leading-relaxed text-justify">
                    {t("about.profileDesc2")}
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
          <div>
            <Card className="bg-card border-border card-hover h-full">
              <CardContent className="p-6 h-full flex flex-col">
                <h3 className="text-xl font-semibold mb-4 text-accent flex items-center">
                  <Heart className="mr-2" />
                  {t("about.personalInfo")}
                </h3>
                <div className="grid sm:grid-cols-2 gap-4 flex-grow">
                  <div>
                    <p className="text-muted-foreground">{t("about.nationality")}</p>
                    <p className="font-semibold">Costa Rica</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">{t("about.languages")}</p>
                    <p className="font-semibold">{t("about.languageProficiency")}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">{t("about.phone")}</p>
                    <a href="tel:+50670391069" className="font-semibold hover:text-accent transition-colors">(506) 7039-1069</a>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </section>
  );
}