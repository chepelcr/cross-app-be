import {Button} from "@/components/ui/button";
import {Download, Mail, ExternalLink} from "lucide-react";
import {useLanguage} from "@/contexts/language-context";
import {downloadCV} from "@/utils/pdf-generator";

export default function HeroSection() {
    const {t, language, cvData, navigateToSection} = useLanguage();

    return (
        <section id="home" className="section-spacing gradient-bg pt-32">
            <div className="container-spacing">
                <div className="flex flex-col lg:flex-row items-center justify-between gap-12">
                    <div className="flex-1 text-center lg:text-left">
                        <h1 className="text-4xl lg:text-6xl font-bold mb-6">
                            Keylor{" "}
                            <span className="text-accent">Lamas Mosquera</span>
                        </h1>
                        <h2 className="text-xl lg:text-2xl text-muted-foreground mb-8">
                            {t("hero.title")} | {t("hero.subtitle")}
                        </h2>
                        <p className="text-lg text-muted-foreground mb-8 max-w-2xl">
                            {t("hero.description")}
                        </p>
                        <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
                            <Button
                                size="lg"
                                className="bg-accent text-accent-foreground hover:bg-accent/90"
                                onClick={() => navigateToSection("contact")}
                            >
                                <Mail className="mr-2 h-4 w-4"/>
                                {t("hero.contactMe")}
                            </Button>
                            <Button
                                variant="outline"
                                size="lg"
                                className="border-accent text-accent hover:bg-accent hover:text-accent-foreground"
                                onClick={() => {
                                    if (cvData) {
                                        downloadCV(cvData, language, t);
                                    } else {
                                        console.log('CV data not ready yet');
                                    }
                                }}
                            >
                                <Download className="mr-2 h-4 w-4"/>
                                {t("hero.downloadCV")}
                            </Button>
                        </div>
                    </div>
                    <div className="flex-1 max-w-md lg:max-w-lg">
                        <img
                            src="https://images.unsplash.com/photo-1555949963-aa79dcee981c?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=800&h=600"
                            alt="Keylor Lamas Mosquera - Professional Profile"
                            className="rounded-xl shadow-2xl w-full h-auto"
                        />
                    </div>
                </div>
            </div>
        </section>
    );
}