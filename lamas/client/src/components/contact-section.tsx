import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { useLanguage } from "@/contexts/language-context";
import { downloadCV } from "@/utils/pdf-generator";
import { 
  Mail, 
  Phone, 
  MapPin, 
  Globe, 
  Send, 
  Download,
  Clock
} from "lucide-react";

const getContactInfo = (t: any) => [
  {
    icon: Phone,
    label: t("contact.phone"),
    value: "(506) 2661-0426",
    href: "tel:+50626610426",
  },
  {
    icon: Mail,
    label: "Email",
    value: "keylorlamasm@gmail.com",
    href: "mailto:keylorlamasm@gmail.com",
  },
  {
    icon: MapPin,
    label: t("contact.location"),
    value: "Costa Rica",
  },
  {
    icon: Globe,
    label: t("contact.website"),
    value: "Costa Rica",
  },
];

const getAvailability = (t: any) => [
  { service: t("contact.freelanceProjects"), status: t("contact.available"), color: "bg-green-500" },
  { service: t("contact.awsConsulting"), status: t("contact.available"), color: "bg-green-500" },
  { service: t("contact.erpDevelopment"), status: t("contact.available"), color: "bg-green-500" },
  { service: t("contact.fullTime"), status: t("contact.considering"), color: "bg-yellow-500" },
];

export default function ContactSection() {
  const { t, language, cvData } = useLanguage();
  const contactInfo = getContactInfo(t);
  const availability = getAvailability(t);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    subject: "",
    message: "",
  });
  const { toast } = useToast();

  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // For GitHub Pages deployment, use mailto link
    const subject = encodeURIComponent(formData.subject || t("contact.defaultSubject"));
    const body = encodeURIComponent(
      `${t("contact.name")}: ${formData.name}\n${t("contact.email")}: ${formData.email}\n\n${formData.message}`
    );
    
    const mailtoLink = `mailto:keylorlamasm@gmail.com?subject=${subject}&body=${body}`;
    window.open(mailtoLink, '_blank');
    
    toast({
      title: t("contact.emailClientTitle"),
      description: t("contact.emailClientDesc"),
    });
    
    // Reset form
    setFormData({ name: "", email: "", subject: "", message: "" });
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <section id="contact" className="section-spacing bg-navy">
      <div className="container-spacing">
        <h2 className="text-3xl lg:text-4xl font-bold text-center mb-16">
          <Mail className="inline-block text-accent mr-4" />
          {t("contact.title")}
        </h2>
        
        <div className="grid lg:grid-cols-2 gap-12 items-start">
          {/* Contact Info */}
          <div className="space-y-8">
            <Card className="bg-card border-border">
              <CardContent className="p-8">
                <h3 className="text-2xl font-semibold mb-6 text-accent">
                  {t("contact.contactInfo")}
                </h3>
                <div className="space-y-6">
                  {contactInfo.map((item, index) => (
                    <div key={index} className="flex items-center space-x-4">
                      <div className="bg-accent text-accent-foreground w-12 h-12 rounded-full flex items-center justify-center">
                        <item.icon className="h-5 w-5" />
                      </div>
                      <div>
                        <p className="font-semibold">{item.label}</p>
                        {item.href ? (
                          <a 
                            href={item.href}
                            className="text-muted-foreground hover:text-accent transition-colors"
                            target={item.href.startsWith("http") ? "_blank" : undefined}
                            rel={item.href.startsWith("http") ? "noopener noreferrer" : undefined}
                          >
                            {item.value}
                          </a>
                        ) : (
                          <p className="text-muted-foreground">{item.value}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-card border-border">
              <CardContent className="p-8">
                <h3 className="text-2xl font-semibold mb-6 text-accent flex items-center">
                  <Clock className="mr-3" />
                  {t("contact.availability")}
                </h3>
                <div className="space-y-4">
                  {availability.map((item, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span>{item.service}</span>
                      <Badge 
                        className={`${item.color} text-white`}
                      >
                        {item.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Contact Form */}
          <Card className="bg-card border-border">
            <CardContent className="p-8">
              <h3 className="text-2xl font-semibold mb-6 text-accent">
                {t("contact.sendMessage")}
              </h3>
              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <Label htmlFor="name">{t("contact.fullName")}</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => handleInputChange("name", e.target.value)}
                    placeholder={t("contact.fullNamePlaceholder")}
                    required
                    className="bg-slate border-border focus:border-accent"
                  />
                </div>
                
                <div>
                  <Label htmlFor="email">{t("contact.email")}</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => handleInputChange("email", e.target.value)}
                    placeholder={t("contact.emailPlaceholder")}
                    required
                    className="bg-slate border-border focus:border-accent"
                  />
                </div>
                
                <div>
                  <Label htmlFor="subject">{t("contact.subject")}</Label>
                  <Select 
                    value={formData.subject} 
                    onValueChange={(value) => handleInputChange("subject", value)}
                  >
                    <SelectTrigger className="bg-slate border-border focus:border-accent">
                      <SelectValue placeholder={t("contact.selectSubject")} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="desarrollo">{t("contact.softwareDev")}</SelectItem>
                      <SelectItem value="aws">{t("contact.awsConsultancy")}</SelectItem>
                      <SelectItem value="erp">{t("contact.erpSystem")}</SelectItem>
                      <SelectItem value="freelance">{t("contact.freelanceProject")}</SelectItem>
                      <SelectItem value="laboral">{t("contact.jobOpportunity")}</SelectItem>
                      <SelectItem value="otro">{t("contact.other")}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Label htmlFor="message">{t("contact.message")}</Label>
                  <Textarea
                    id="message"
                    value={formData.message}
                    onChange={(e) => handleInputChange("message", e.target.value)}
                    placeholder={t("contact.messagePlaceholder")}
                    rows={5}
                    required
                    className="bg-slate border-border focus:border-accent resize-none"
                  />
                </div>
                
                <Button 
                  type="submit" 
                  disabled={isSubmitting}
                  className="w-full bg-accent text-accent-foreground hover:bg-accent/90 disabled:opacity-50"
                >
                  <Send className="mr-2 h-4 w-4" />
                  {isSubmitting ? t("contact.sending") : t("contact.send")}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Download CV Section */}
        <div className="mt-16 text-center">
          <Card className="bg-card border-border inline-block">
            <CardContent className="p-8">
              <h3 className="text-xl font-semibold mb-4 text-accent">
                {t("contact.downloadCV")}
              </h3>
              <p className="text-muted-foreground mb-6">
                {t("contact.downloadCVDesc")}
              </p>
              <Button
                className="bg-accent text-accent-foreground hover:bg-accent/90"
                onClick={() => {
                    if (cvData) {
                        downloadCV(cvData, language, t);
                    } else {
                        console.log('CV data not ready yet');
                    }
                }}
              >
                <Download className="mr-2 h-4 w-4" />
                {t("hero.downloadCV")}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
}