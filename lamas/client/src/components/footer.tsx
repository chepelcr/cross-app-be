import { Mail, Phone, Globe, Linkedin, Github, Heart } from "lucide-react";
import { useLanguage } from "@/contexts/language-context";

const socialLinks = [
  {
    icon: Mail,
    href: "mailto:keylorlamasm@gmail.com",
    label: "Email",
  },
  {
    icon: Phone,
    href: "tel:+50626610426",
    label: "Phone",
  },
];

export default function Footer() {
  const { t } = useLanguage();
  
  return (
    <footer className="bg-slate border-t border-border py-12">
      <div className="container-spacing">
        <div className="text-center">
          <div className="mb-8">
            <h3 className="text-2xl font-bold text-accent mb-4">
              Keylor Lamas Mosquera
            </h3>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              {t("footer.description")}
            </p>
          </div>
          
          {/* Social Links */}
          <div className="flex justify-center space-x-6 mb-8">
            {socialLinks.map((link, index) => (
              <a
                key={index}
                href={link.href}
                className="bg-card hover:bg-accent hover:text-accent-foreground w-12 h-12 rounded-full flex items-center justify-center transition-colors"
                target={link.href.startsWith("http") ? "_blank" : undefined}
                rel={link.href.startsWith("http") ? "noopener noreferrer" : undefined}
                aria-label={link.label}
              >
                <link.icon className="h-5 w-5" />
              </a>
            ))}
          </div>
          
          <div className="border-t border-border pt-8">
            <p className="text-muted-foreground">
              &copy; 2024 Keylor Lamas Mosquera. {t("footer.rights")}
            </p>
            <p className="text-muted-foreground text-sm mt-2 flex items-center justify-center">
              {t("footer.developedWith")} <Heart className="h-4 w-4 text-red-500 mx-1" /> {t("footer.modernTech")}
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}