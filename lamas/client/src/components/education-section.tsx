import {Card, CardContent} from "@/components/ui/card";
import {Badge} from "@/components/ui/badge";
import {useLanguage} from "@/contexts/language-context";
import {GraduationCap, Award, BookOpen, ExternalLink} from "lucide-react";

const getEducation = (t: any) => [
    {
        degree: t("education.businessInformatics"),
        institution: "Universidad de Costa Rica, Sede del Pacífico",
        period: "2017 - 2022",
    },
    {
        degree: t("education.internationalBaccalaureate"),
        institution: "Liceo de Costa Rica",
        period: "2015 - 2016",
    },
    {
        degree: t("education.mediaEducation"),
        institution: "Liceo de Costa Rica",
        period: "2010 - 2016",
    },
];

const certifications = [
    {
        name: "AWS Certified Solutions Architect",
        provider: "AWS",
        date: "13-04-2023",
        description: "Certificación de nivel asociado en arquitectura de soluciones AWS",
        badge: "AWS",
        verifyUrl: "https://www.credly.com/badges/44e22e53-62a4-4bd5-9211-12d3b428623a/linked_in_profile",
    },
    {
        name: "AWS Certified Cloud Practitioner",
        provider: "AWS",
        date: "16-02-2023",
        description: "Certificación fundamental de servicios y conceptos de AWS",
        badge: "AWS",
        verifyUrl: "https://www.credly.com/badges/2c7deda1-87a3-44c5-aa78-324803af975c/linked_in_profile",
    },
    {
        name: "Microsoft Certified: Azure Fundamentals",
        provider: "Azure",
        date: "22-03-2023",
        description: "Certificación fundamental de servicios de Microsoft Azure",
        badge: "Azure",
        verifyUrl: "https://www.credly.com/badges/58f0d676-95d7-409f-bb29-16219c4b982b/linked_in_profile",
    },
    {
        name: "CCNA: Introduction to Networks",
        provider: "Cisco",
        date: "2023",
        description: "Certificación en fundamentos de redes y tecnologías Cisco",
        badge: "Cisco",
        verifyUrl: "https://www.youracclaim.com/badges/9c7bdce0-a8f3-4502-9ec2-efd607822f72?source=linked_in_profile",
    },
    {
        name: "EF SET English Certificate",
        provider: "EF Education First",
        date: "2023",
        description: "Certificación de nivel de inglés - Nivel B2",
        badge: "EF SET",
        verifyUrl: "https://www.efset.org/cert/Km8PLK",
    },
];

const training = [
    {
        institution: "Academia de Tecnología UCR",
        courses: ["CCNAv7: Introduction to networks", "NDG Linux I"],
    },
    {
        institution: "Centro Comunitario Miramar",
        courses: ["PHP – Electronic Billing – Hacienda", "Inteligencia Artificial", "Advanced Excel"],
    },
    {
        institution: "AWS Skill Builder",
        courses: ["AWS Cloud Practitioner Essentials", "AWS Security Fundamentals", "AWS Well-Architected Best Practices"],
    },
];

export default function EducationSection() {
    const {t} = useLanguage();
    const education = getEducation(t);

    return (
        <section id="education" className="section-spacing bg-navy">
            <div className="container-spacing">
                <h2 className="text-3xl lg:text-4xl font-bold text-center mb-16">
                    <GraduationCap className="inline-block text-accent mr-4"/>
                    {t("education.title")}
                </h2>

                {/* Certifications Section */}
                <div className="mb-16">
                    <h3 className="text-2xl font-semibold mb-8 text-accent text-center flex items-center justify-center">
                        <Award className="mr-3"/>
                        {t("education.certificationsSubtitle")}
                    </h3>
                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {certifications.map((cert, index) => (
                            <Card key={index} className="bg-card border-border card-hover h-full">
                                <CardContent className="p-6 h-full flex flex-col">
                                    <div className="flex items-start justify-between mb-4">
                                        <h4 className="text-lg font-semibold pr-2 leading-tight flex-grow">{cert.name}</h4>
                                        <Badge className="bg-accent text-accent-foreground flex-shrink-0 ml-2">
                                            {cert.badge}
                                        </Badge>
                                    </div>
                                    <div className="mb-3">
                                        <p className="text-muted-foreground font-mono text-sm">
                                            {t("education.activationDate")} {cert.date}
                                        </p>
                                    </div>
                                    <p className="text-muted-foreground text-sm mb-6 flex-grow leading-relaxed">{cert.description}</p>
                                    {cert.verifyUrl && (
                                        <div className="mt-auto">
                                            <a
                                                href={cert.verifyUrl}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="inline-flex items-center px-4 py-2 bg-accent/10 border border-accent/20 rounded-lg text-accent hover:bg-accent hover:text-white text-sm font-medium transition-colors duration-200 w-full justify-center gap-2"
                                            >
                                                <ExternalLink className="h-4 w-4"/>
                                                {t("education.verifyCredential")}
                                            </a>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </div>

                {/* Education Section */}
                <div className="mb-16">
                    <h3 className="text-2xl font-semibold mb-8 text-accent text-center flex items-center justify-center">
                        <GraduationCap className="mr-3"/>
                        {t("education.educationSubtitle")}
                    </h3>
                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {education.map((edu, index) => (
                            <Card key={index} className="bg-card border-border card-hover h-full">
                                <CardContent className="p-6 h-full flex flex-col">
                                    <div className="min-h-[3.5rem] mb-3">
                                        <h4 className="text-lg font-semibold leading-tight">{edu.degree}</h4>
                                    </div>
                                    <p className="text-accent font-medium mb-3 flex-grow">{edu.institution}</p>
                                    <p className="text-muted-foreground font-mono text-sm">{edu.period}</p>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </div>

                {/* Training Section */}
                <div>
                    <h3 className="text-2xl font-semibold mb-8 text-accent text-center flex items-center justify-center">
                        <BookOpen className="mr-3"/>
                        {t("education.trainingSubtitle")}
                    </h3>
                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {training.map((item, index) => (
                            <Card key={index} className="bg-card border-border card-hover">
                                <CardContent className="p-4">
                                    <h4 className="font-semibold mb-2">{item.institution}</h4>
                                    <ul className="text-sm text-muted-foreground space-y-1">
                                        {item.courses.map((course, courseIndex) => (
                                            <li key={courseIndex}>• {course}</li>
                                        ))}
                                    </ul>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </div>
            </div>
        </section>
    );
}