import {createContext, useContext, useState, useEffect, ReactNode, useMemo} from "react";
import {useLocation} from "wouter";

export type Language = "es" | "en";
export type Section = "home" | "about" | "skills" | "experience" | "education" | "projects" | "contact";

export interface CVData {
  personalInfo: {
    name: string;
    title: string;
    email: string;
    phone: string;
    location: string;
    languages: string;
  };
  about: string;
  experience: Array<{
    title: string;
    company: string;
    period: string;
    description: string;
    skills: string[];
  }>;
  education: Array<{
    degree: string;
    institution: string;
    period: string;
  }>;
  certifications: Array<{
    name: string;
    date: string;
  }>;
  additionalTraining: Array<{
    name: string;
    institution: string;
    date: string;
  }>;
  skills: {
    backend: string[];
    cloud: string[];
    databases: string[];
    tools: string[];
  };
  projects: Array<{
    name: string;
    description: string;
    technologies: string[];
  }>;
}

type LanguageContextType = {
    language: Language;
    currentSection: Section | null;
    cvData: CVData;
    setLanguage: (lang: Language) => void;
    navigateToSection: (section: Section, updateUrl?: boolean) => void;
    t: (key: string) => string;
};

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const useLanguage = () => {
    const context = useContext(LanguageContext);
    if (!context) {
        throw new Error("useLanguage must be used within a LanguageProvider");
    }
    return context;
};

type LanguageProviderProps = {
    children: ReactNode;
};

export function LanguageProvider({children}: LanguageProviderProps) {
    const [location, navigate] = useLocation();
    const [language, setLanguageState] = useState<Language>("es");
    const [currentSection, setCurrentSection] = useState<Section | null>(null);

    // Parse language and section from URL
    useEffect(() => {
        const pathParts = location.split('/').filter(Boolean);
        const urlLang = pathParts[0] as Language;
        const urlSection = pathParts[1] as Section;

        if (urlLang === "es" || urlLang === "en") {
            setLanguageState(urlLang);
            localStorage.setItem("portfolio-language", urlLang);
            setCurrentSection(urlSection || "home");
        }
    }, [location]);

    const setLanguage = (lang: Language) => {
        // Don't transition if already on the selected language
        if (lang === language) {
            return;
        }

        // Get current scroll position to maintain it
        const currentScrollY = window.scrollY;

        // Prevent any scrolling during transition
        document.body.style.overflow = 'hidden';
        document.body.style.position = 'fixed';
        document.body.style.top = `-${currentScrollY}px`;
        document.body.style.width = '100%';

        // Add slide-out animation
        document.body.classList.add("language-transitioning");

        setTimeout(() => {
            const pathParts = location.split('/').filter(Boolean);
            const currentSectionFromUrl = pathParts[1] || "home";

            setLanguageState(lang);
            localStorage.setItem("portfolio-language", lang);

            // Navigate to new language with current section
            const newPath = currentSectionFromUrl === "home" ? `/${lang}` : `/${lang}/${currentSectionFromUrl}`;
            navigate(newPath);

            // Add slide-in animation
            document.body.classList.remove("language-transitioning");
            document.body.classList.add("slide-in");

            // Remove slide-in class and restore scroll after animation
            setTimeout(() => {
                document.body.classList.remove("slide-in");

                // Restore scroll position and body styles
                document.body.style.overflow = '';
                document.body.style.position = '';
                document.body.style.top = '';
                document.body.style.width = '';
                window.scrollTo({top: currentScrollY, behavior: 'instant'});
            }, 300);
        }, 300);
    };

    const navigateToSection = (section: Section, updateUrl: boolean = true) => {
        setCurrentSection(section);
        if (updateUrl) {
            const newPath = section === "home" ? `/${language}` : `/${language}/${section}`;
            navigate(newPath);
        }

        // Scroll to the section
        const element = document.getElementById(section);
        if (element) {
            const headerOffset = 80; // Account for fixed navigation
            const elementPosition = element.offsetTop;
            const offsetPosition = elementPosition - headerOffset;

            window.scrollTo({
                top: offsetPosition,
                behavior: 'smooth'
            });
        }
    };

    const t = (key: string): string => {
        const translation = translations[language] as Record<string, string>;
        return translation[key] || key;
    };

    const cvData: CVData = useMemo(() => ({
        personalInfo: {
            name: 'Keylor Lamas Mosquera',
            title: t('hero.title'),
            email: 'keylorlamasm@gmail.com',
            phone: '(506) 2661-0426',
            location: 'Costa Rica',
            languages: t('about.languageProficiency')
        },
        about: t('about.description'),
        experience: [
            {
                title: t('experience.deliveryDriverTitle'),
                company: t('experience.deliveryDriverCompany'),
                period: t('experience.deliveryDriverPeriod'),
                description: t('experience.deliveryDriverDesc'),
                skills: ['GPS Navigation', 'Route Planning', 'Cash Handling', 'Digital Payments', 'Customer Service', 'Order Management']
            },
            {
                title: t('experience.customerServiceTitle'),
                company: t('experience.customerServiceCompany'),
                period: t('experience.customerServicePeriod'),
                description: t('experience.customerServiceDesc'),
                skills: ['POS Systems', 'Inventory Management', 'Bilingual Communication', 'Customer Support', 'Product Knowledge', 'Transaction Processing']
            }
        ],
        education: [
            {
                degree: t('education.highSchool'),
                institution: 'Colegio Nocturno José Martí, Puntarenas',
                period: '2022'
            },
            {
                degree: t('education.primarySchool'),
                institution: 'El Carmen School, Puntarenas',
                period: '2002 - 2008'
            }
        ],
        certifications: [],
        additionalTraining: [
            {
                name: language === 'es' ? 'Inglés ejecutivo para servicios' : 'Executive English for Services',
                institution: 'Instituto Nacional de Aprendizaje',
                date: ''
            },
            {
                name: language === 'es' ? 'Nivel 1 Principiante, 80 hrs' : 'Level 1 Beginner, 80 hrs',
                institution: 'Educational Language Corporation',
                date: ''
            }
        ],
        skills: {
            backend: language === 'es' 
                ? ['Sistemas POS', 'Microsoft Office', 'Comunicación Básica en Inglés']
                : ['POS Systems', 'Microsoft Office', 'Basic English Communication'],
            cloud: language === 'es'
                ? ['Navegación GPS', 'Apps de Entrega de Comida', 'Procesamiento de Pagos']
                : ['GPS Navigation', 'Food Delivery Apps', 'Payment Processing'],
            databases: language === 'es'
                ? ['Gestión de Inventario', 'Plataformas CRM', 'Herramientas de Gestión de Pedidos']
                : ['Inventory Management', 'CRM Platforms', 'Order Management Tools'],
            tools: language === 'es'
                ? ['Reconciliación de Efectivo', 'Planificación de Rutas', 'Herramientas de Soporte al Cliente']
                : ['Cash Reconciliation', 'Route Planning', 'Customer Support Tools']
        },
        projects: [
            {
                name: t('projects.beautyMarketTitle'),
                description: t('projects.beautyMarketDesc'),
                technologies: ['React', 'TypeScript', 'Node.js', 'AWS Lambda', 'PostgreSQL', 'Cognito', 'CloudFormation']
            },
            {
                name: t('projects.videoTranscriptTitle'),
                description: t('projects.videoTranscriptDesc'),
                technologies: ['React', 'TypeScript', 'AI Services', 'Web APIs']
            },
            {
                name: t('projects.linuxTitle'),
                description: t('projects.linuxDesc'),
                technologies: ['React', 'TypeScript', 'Tailwind CSS', 'Node.js']
            }
        ]
    }), [language, t]);

    return (
        <LanguageContext.Provider value={{language, currentSection, cvData, setLanguage, navigateToSection, t}}>
            {children}
        </LanguageContext.Provider>
    );
}

const translations = {
    es: {
        // Navigation
        "nav.home": "Inicio",
        "nav.about": "Acerca de",
        "nav.skills": "Habilidades",
        "nav.experience": "Experiencia",
        "nav.education": "Educación",
        "nav.projects": "Proyectos",
        "nav.contact": "Contacto",

        // Hero Section
        "hero.greeting": "¡Hola! Soy",
        "hero.title": "Representante de Servicio al Cliente",
        "hero.subtitle": "Soporte Bilingüe",
        "hero.description": "Representante de servicio al cliente dedicado con experiencia en atención bilingüe, gestión de pedidos y resolución de problemas. Comprometido con brindar experiencias excepcionales al cliente.",
        "hero.contactMe": "Contáctame",
        "hero.downloadCV": "Descargar CV",

        // About Section
        "about.title": "Acerca de Mí",
        "about.description": "Soy un representante de servicio al cliente dedicado con diploma de secundaria y habilidades básicas de inglés, con experiencia en atención a clientes de habla hispana e inglesa. Con experiencia en una licorería de alto tráfico y entrega de comida rápida, he perfeccionado mi capacidad para resolver consultas eficientemente, gestionar problemas de pedidos y mantener una comunicación clara y oportuna.",
        "about.yearsExperience": "Años de Experiencia",
        "about.projectsCompleted": "Proyectos Completados",
        "about.certifications": "Certificaciones",
        "about.professionalProfile": "Perfil Profesional",
        "about.personalInfo": "Información Personal",
        "about.nationality": "Nacionalidad:",
        "about.languages": "Idiomas:",
        "about.languageProficiency": "Español (Nativo), Inglés (A1)",
        "about.phone": "Teléfono:",
        "about.id": "ID:",
        "about.profileDesc1": "Representante de servicio al cliente con experiencia en sistemas POS, plataformas CRM y herramientas de gestión de pedidos en línea.",
        "about.profileDesc3": "Experto en rastreo de pedidos, resolución de problemas y garantía de satisfacción del cliente en entornos de alto volumen.",
        "about.profileDesc2": "Impulsado por la adaptabilidad y empatía, estoy comprometido con el aprendizaje continuo y la entrega de experiencias excepcionales al cliente en todos los canales.",

        // Skills Section
        "skills.title": "Habilidades Técnicas",
        "skills.backend": "Sistemas y Herramientas",
        "skills.cloud": "Tecnología y Navegación",
        "skills.databases": "Gestión y Plataformas",
        "skills.tools": "Habilidades Operativas",
        "skills.softSkills": "Habilidades Blandas",
        "skills.analyticalThinking": "Comunicador Bilingüe Efectivo",
        "skills.analyticalDesc": "Comunicación clara en español e inglés básico",
        "skills.teamwork": "Constructor de Relaciones",
        "skills.teamworkDesc": "Excelente en establecer rapport con clientes",
        "skills.adaptability": "Adaptabilidad y Resiliencia",
        "skills.adaptabilityDesc": "Flexible ante cambios y desafíos",
        "skills.initiative": "Solucionador Proactivo",
        "skills.initiativeDesc": "Enfoque proactivo en resolución de problemas",
        "skills.expert": "Experto",
        "skills.advanced": "Avanzado",
        "skills.intermediate": "Intermedio",
        "skills.basic": "Básico",
        "skills.certified": "Certificado",
        "cv.technologies": "Tecnologías:",
        "cv.page": "Página",

        // Experience Section
        "experience.title": "Experiencia Profesional",
        "experience.current": "Actual",
        "experience.deliveryDriverTitle": "Conductor de Entregas",
        "experience.deliveryDriverCompany": "Soda Munchies",
        "experience.deliveryDriverPeriod": "Junio 2023 - Presente",
        "experience.deliveryDriverDesc": "Coordiné rutas de entrega eficientes utilizando navegación GPS para garantizar entregas puntuales." +
            "\nAseguré la precisión de los pedidos y manejé pagos en efectivo y digitales con reconciliación precisa." +
            "\nResolví consultas de clientes rápidamente, manteniendo altos niveles de satisfacción del cliente." +
            "\nMantuve comunicación clara con clientes y el equipo del restaurante para actualizaciones de pedidos.",
        "experience.customerServiceTitle": "Asociado de Servicio al Cliente",
        "experience.customerServiceCompany": "Licorera las Brisas",
        "experience.customerServicePeriod": "Marzo 2015 - Mayo 2016",
        "experience.customerServiceDesc": "Asistí a turistas internacionales con selección de productos y procesé transacciones utilizando sistemas POS." +
            "\nGestioné inventario y reabastecimiento, asegurando disponibilidad de productos y organización de la tienda." +
            "\nComuniqué efectivamente en español e inglés básico con clientes diversos." +
            "\nManejé múltiples responsabilidades en un entorno de alto tráfico manteniendo un servicio de calidad.",

        // Education Section
        "education.title": "Educación y Capacitación",
        "education.educationSubtitle": "Educación",
        "education.certificationsSubtitle": "Certificaciones",
        "education.trainingSubtitle": "Capacitaciones Adicionales",
        "education.activationDate": "Fecha de activación:",
        "education.verifyCredential": "Verificar Certificación",
        "education.highSchool": "Bachiller en Educación Media",
        "education.primarySchool": "Educación Primaria",

        // Projects Section
        "projects.title": "Proyectos Destacados",
        "projects.viewProject": "Ver Proyecto",
        "projects.viewCode": "Ver Código",
        "projects.enterERP": "Entrar",
        "projects.beautyMarketTitle": "BeautyMarket - Plataforma SaaS",
        "projects.beautyMarketDesc": "Plataforma SaaS multi-tenant para gestión de productos de belleza con arquitectura serverless completa en AWS. Incluye autenticación con Cognito, gestión de contenido CMS, dashboard administrativo y soporte multi-idioma.",
        "projects.beautyMarketFeature1": "Arquitectura multi-tenant con aislamiento completo",
        "projects.beautyMarketFeature2": "Infraestructura serverless escalable en AWS",
        "projects.beautyMarketFeature3": "Sistema CMS integrado para gestión de contenido",
        "projects.beautyMarketFeature4": "CI/CD automatizado con CodePipeline",
        "projects.erpTitle": "Sistema ERP para Facturación Electrónica",
        "projects.erpDesc": "Sistema integral de gestión empresarial desarrollado con arquitectura de microservicios. Incluye facturación electrónica integrada con IVOIS, gestión de inventario y reportes básicos.",
        "projects.videoTranscriptTitle": "Transcripción de Video con IA",
        "projects.videoTranscriptDesc": "Herramienta inteligente que extrae automáticamente el texto y subtítulos de videos utilizando servicios de inteligencia artificial avanzados. Soporta múltiples formatos de video y proporciona transcripciones precisas en tiempo real.",
        "projects.videoFeature1": "Transcripción automática con IA",
        "projects.videoFeature2": "Soporte para múltiples formatos",
        "projects.videoFeature3": "Interface multiidioma",
        "projects.videoFeature4": "Exportación de subtítulos",
        "projects.linuxTitle": "Sitio Web de Comandos Linux",
        "projects.linuxDesc": "Plataforma educativa interactiva para aprender comandos básicos de Linux. Incluye conceptos fundamentales, ejemplos prácticos, herramientas de administración y utilidades para desarrolladores y administradores de sistemas.",
        "projects.feature1": "Interface interactiva y responsive",
        "projects.feature2": "Ejemplos de comandos categorizados",
        "projects.feature3": "Guías de seguridad informática",
        "projects.feature4": "Herramientas de administración",
        "projects.ecommerceTitle": "E-commerce API",
        "projects.ecommerceDesc": "API REST para plataforma de comercio electrónico",
        "projects.dashboardTitle": "Dashboard de Analytics",
        "projects.dashboardDesc": "Panel de control para análisis de datos empresariales",
        "projects.characteristics": "Características:",
        "projects.technologies": "Tecnologías:",
        "projects.technologiesUsed": "Tecnologías Utilizadas:",
        "projects.otherProjects": "Otros Proyectos",
        "projects.visitSite": "Visitar Sitio",
        "projects.viewDetails": "Ver Detalles",
        "projects.viewAllProjects": "Ver Todos los Proyectos",

        // Contact Section
        "contact.title": "Contáctame",
        "contact.subtitle": "¿Tienes un proyecto en mente? ¡Hablemos!",
        "contact.description": "Estoy siempre interesado en nuevas oportunidades y proyectos desafiantes. No dudes en contactarme.",
        "contact.name": "Nombre",
        "contact.email": "Correo Electrónico",
        "contact.subject": "Asunto",
        "contact.message": "Mensaje",
        "contact.send": "Enviar Mensaje",
        "contact.sending": "Enviando...",
        "contact.success": "¡Mensaje enviado exitosamente!",
        "contact.error": "Error al enviar el mensaje. Inténtalo de nuevo.",
        "contact.phone": "Teléfono",
        "contact.location": "Ubicación",
        "contact.website": "Sitio Web",
        "contact.availability": "Disponibilidad",
        "contact.freelanceProjects": "Proyectos Freelance",
        "contact.awsConsulting": "Consultorías AWS",
        "contact.erpDevelopment": "Desarrollo de ERP",
        "contact.fullTime": "Tiempo Completo",
        "contact.available": "Disponible",
        "contact.considering": "Considerando",
        "contact.contactInfo": "Información de Contacto",
        "contact.messageSentTitle": "¡Mensaje enviado!",
        "contact.messageSentDesc": "Te contactaré pronto. Gracias por tu interés.",
        "contact.errorSendingTitle": "Error al enviar mensaje",
        "contact.errorSendingDesc": "Hubo un problema al enviar tu mensaje. Por favor intenta más tarde.",
        "contact.connectionErrorTitle": "Error de conexión",
        "contact.connectionErrorDesc": "No se pudo conectar con el servidor. Verifica tu conexión e intenta nuevamente.",
        "contact.sendMessage": "Envíame un Mensaje",
        "contact.fullName": "Nombre Completo",
        "contact.fullNamePlaceholder": "Tu nombre completo",
        "contact.emailPlaceholder": "tu@email.com",
        "contact.selectSubject": "Selecciona un asunto",
        "contact.messagePlaceholder": "Describe tu proyecto o consulta...",
        "contact.softwareDev": "Desarrollo de Software",
        "contact.awsConsultancy": "Consultoría AWS",
        "contact.erpSystem": "Sistema ERP",
        "contact.freelanceProject": "Proyecto Freelance",
        "contact.jobOpportunity": "Oportunidad Laboral",
        "contact.other": "Otro",
        "contact.downloadCV": "Descarga mi CV",
        "contact.downloadCVDesc": "Obtén una copia completa de mi currículum vitae",
        "contact.defaultSubject": "Contacto desde el portafolio",
        "contact.emailClientTitle": "Cliente de email abierto",
        "contact.emailClientDesc": "Se ha abierto tu cliente de email predeterminado con el mensaje preparado.",

        // Common
        "common.back": "Volver",

        // Footer
        "footer.description": "Desarrollador de software especializado en soluciones Backend con Java, Python y AWS. Creando sistemas escalables que impulsan el crecimiento empresarial.",
        "footer.rights": "Todos los derechos reservados.",
        "footer.developedWith": "Desarrollado con",
        "footer.modernTech": "utilizando tecnologías modernas",
    },
    en: {
        // Navigation
        "nav.home": "Home",
        "nav.about": "About",
        "nav.skills": "Skills",
        "nav.experience": "Experience",
        "nav.education": "Education",
        "nav.projects": "Projects",
        "nav.contact": "Contact",

        // Hero Section
        "hero.greeting": "Hello! I'm",
        "hero.title": "Customer Service Representative",
        "hero.subtitle": "Bilingual Support",
        "hero.description": "Dedicated customer service representative with experience in bilingual support, order management, and problem resolution. Committed to delivering exceptional customer experiences.",
        "hero.contactMe": "Contact Me",
        "hero.downloadCV": "Download CV",

        // About Section
        "about.title": "About Me",
        "about.description": "I am a dedicated customer service representative with a high school diploma and foundational English skills, experienced in supporting both Spanish- and English-speaking customers. With a background in a high-traffic liquor store and fast-food delivery, I've honed my ability to resolve inquiries efficiently, manage order issues, and maintain clear, timely communication.",
        "about.yearsExperience": "Years of Experience",
        "about.projectsCompleted": "Projects Completed",
        "about.certifications": "Certifications",
        "about.professionalProfile": "Professional Profile",
        "about.personalInfo": "Personal Information",
        "about.nationality": "Nationality:",
        "about.languages": "Languages:",
        "about.languageProficiency": "Spanish (Native), English (A1)",
        "about.phone": "Phone:",
        "about.id": "ID:",
        "about.profileDesc1": "Customer service representative with experience in POS systems, CRM platforms, and online order management tools.",
        "about.profileDesc3": "Proficient in tracking orders, troubleshooting concerns, and ensuring customer satisfaction in high-volume environments.",
        "about.profileDesc2": "Driven by adaptability and empathy, I'm committed to continuous learning and delivering exceptional customer experiences across all channels.",

        // Skills Section
        "skills.title": "Technical Skills",
        "skills.backend": "Systems & Tools",
        "skills.cloud": "Technology & Navigation",
        "skills.databases": "Management & Platforms",
        "skills.tools": "Operational Skills",
        "skills.softSkills": "Soft Skills",
        "skills.analyticalThinking": "Effective Bilingual Communicator",
        "skills.analyticalDesc": "Clear communication in Spanish and basic English",
        "skills.teamwork": "Excellent Rapport-Builder",
        "skills.teamworkDesc": "Strong at establishing customer relationships",
        "skills.adaptability": "Adaptability & Resilience",
        "skills.adaptabilityDesc": "Flexible in facing changes and challenges",
        "skills.initiative": "Proactive Problem-Solver",
        "skills.initiativeDesc": "Proactive approach to problem resolution",
        "skills.expert": "Expert",
        "skills.advanced": "Advanced",
        "skills.intermediate": "Intermediate",
        "skills.basic": "Basic",
        "skills.certified": "Certified",
        "cv.technologies": "Technologies:",
        "cv.page": "Page",

        // Experience Section
        "experience.title": "Professional Experience",
        "experience.current": "Current",
        "experience.deliveryDriverTitle": "Delivery Driver",
        "experience.deliveryDriverCompany": "Soda Munchies",
        "experience.deliveryDriverPeriod": "June 2023 - Present",
        "experience.deliveryDriverDesc": "Coordinated efficient delivery routes using GPS navigation to ensure timely deliveries." +
            "\nEnsured order accuracy and handled cash and digital payments with accurate reconciliation." +
            "\nResolved customer inquiries promptly, maintaining high customer satisfaction levels." +
            "\nMaintained clear communication with customers and restaurant team for order updates.",
        "experience.customerServiceTitle": "Customer Service Associate",
        "experience.customerServiceCompany": "Licorera las Brisas",
        "experience.customerServicePeriod": "March 2015 - May 2016",
        "experience.customerServiceDesc": "Assisted international tourists with product selection and processed transactions using POS systems." +
            "\nManaged inventory and restocking, ensuring product availability and store organization." +
            "\nCommunicated effectively in Spanish and basic English with diverse customers." +
            "\nHandled multiple responsibilities in a high-traffic environment while maintaining quality service.",

        // Education Section
        "education.title": "Education and Training",
        "education.educationSubtitle": "Education",
        "education.certificationsSubtitle": "Certifications",
        "education.trainingSubtitle": "Additional Training",
        "education.activationDate": "Activation date:",
        "education.verifyCredential": "Verify Certification",
        "education.highSchool": "High School Diploma",
        "education.primarySchool": "Primary Education",

        // Projects Section
        "projects.title": "Featured Projects",
        "projects.viewProject": "View Project",
        "projects.viewCode": "View Code",
        "projects.enterERP": "Enter",
        "projects.beautyMarketTitle": "BeautyMarket - SaaS Platform",
        "projects.beautyMarketDesc": "Multi-tenant SaaS platform for beauty product management with complete serverless architecture on AWS. Includes Cognito authentication, CMS content management, administrative dashboard and multi-language support.",
        "projects.beautyMarketFeature1": "Multi-tenant architecture with complete isolation",
        "projects.beautyMarketFeature2": "Scalable serverless infrastructure on AWS",
        "projects.beautyMarketFeature3": "Integrated CMS system for content management",
        "projects.beautyMarketFeature4": "Automated CI/CD with CodePipeline",
        "projects.erpTitle": "ERP System for Electronic Invoicing",
        "projects.erpDesc": "Comprehensive business management system developed with microservices architecture. Includes electronic invoicing integrated with IVOIS, inventory management and basic reporting.",
        "projects.videoTranscriptTitle": "AI Video Transcription",
        "projects.videoTranscriptDesc": "Intelligent tool that automatically extracts text and subtitles from videos using advanced artificial intelligence services. Supports multiple video formats and provides accurate real-time transcriptions.",
        "projects.videoFeature1": "Automatic AI transcription",
        "projects.videoFeature2": "Multiple format support",
        "projects.videoFeature3": "Multilingual interface",
        "projects.videoFeature4": "Subtitle export",
        "projects.linuxTitle": "Linux Commands Website",
        "projects.linuxDesc": "Interactive educational platform for learning basic Linux commands. Includes fundamental concepts, practical examples, administration tools and utilities for developers and system administrators.",
        "projects.feature1": "Interactive and responsive interface",
        "projects.feature2": "Categorized command examples",
        "projects.feature3": "Information security guides",
        "projects.feature4": "Administration tools",
        "projects.ecommerceTitle": "E-commerce API",
        "projects.ecommerceDesc": "REST API for e-commerce platform",
        "projects.dashboardTitle": "Analytics Dashboard",
        "projects.dashboardDesc": "Control panel for business data analysis",
        "projects.characteristics": "Features:",
        "projects.technologies": "Technologies:",
        "projects.technologiesUsed": "Technologies Used:",
        "projects.otherProjects": "Other Projects",
        "projects.visitSite": "Visit Site",
        "projects.viewAllProjects": "View All Projects",
        "projects.viewDetails": "View Details",

        // Contact Section
        "contact.title": "Contact Me",
        "contact.subtitle": "Have a project in mind? Let's talk!",
        "contact.description": "I'm always interested in new opportunities and challenging projects. Don't hesitate to contact me.",
        "contact.name": "Name",
        "contact.email": "Email",
        "contact.subject": "Subject",
        "contact.message": "Message",
        "contact.send": "Send Message",
        "contact.sending": "Sending...",
        "contact.success": "Message sent successfully!",
        "contact.error": "Error sending message. Please try again.",
        "contact.phone": "Phone",
        "contact.location": "Location",
        "contact.website": "Website",
        "contact.availability": "Availability",
        "contact.freelanceProjects": "Freelance Projects",
        "contact.awsConsulting": "AWS Consulting",
        "contact.erpDevelopment": "ERP Development",
        "contact.fullTime": "Full Time",
        "contact.available": "Available",
        "contact.considering": "Considering",
        "contact.contactInfo": "Contact Information",
        "contact.messageSentTitle": "Message sent!",
        "contact.messageSentDesc": "I'll contact you soon. Thanks for your interest.",
        "contact.errorSendingTitle": "Error sending message",
        "contact.errorSendingDesc": "There was a problem sending your message. Please try again later.",
        "contact.connectionErrorTitle": "Connection error",
        "contact.connectionErrorDesc": "Could not connect to the server. Check your connection and try again.",
        "contact.sendMessage": "Send me a Message",
        "contact.fullName": "Full Name",
        "contact.fullNamePlaceholder": "Your full name",
        "contact.emailPlaceholder": "your@email.com",
        "contact.selectSubject": "Select a subject",
        "contact.messagePlaceholder": "Describe your project or inquiry...",
        "contact.softwareDev": "Software Development",
        "contact.awsConsultancy": "AWS Consulting",
        "contact.erpSystem": "ERP System",
        "contact.freelanceProject": "Freelance Project",
        "contact.jobOpportunity": "Job Opportunity",
        "contact.other": "Other",
        "contact.downloadCV": "Download my CV",
        "contact.downloadCVDesc": "Get a complete copy of my curriculum vitae",
        "contact.defaultSubject": "Contact from portfolio",
        "contact.emailClientTitle": "Email client opened",
        "contact.emailClientDesc": "Your default email client has been opened with the prepared message.",

        // Common
        "common.back": "Back",

        // Footer
        "footer.description": "Software developer specialized in Backend solutions with Java, Python and AWS. Creating scalable systems that drive business growth.",
        "footer.rights": "All rights reserved.",
        "footer.developedWith": "Developed with",
        "footer.modernTech": "using modern technologies",
    },
};