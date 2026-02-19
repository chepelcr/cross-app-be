import jsPDF from 'jspdf';
import { CVData } from '@/contexts/language-context';

export function generatePDF(data: CVData, language: 'es' | 'en', t: (key: string) => string) {
  const doc = new jsPDF();
  let yPosition = 20;
  let currentColumn = 1; // 1 for left, 2 for right
  let isSecondPage = false;
  const pageWidth = doc.internal.pageSize.width;
  const margin = 20;
  const contentWidth = pageWidth - 2 * margin;
  const columnWidth = (contentWidth - 10) / 2; // 10 for column gap
  const leftColumnX = margin;
  const rightColumnX = margin + columnWidth + 10;

  // Colors
  const primaryColor = '#1e3a8a'; // Dark blue accent
  const textColor = '#374151';
  const lightTextColor = '#6b7280';

  // Helper functions
  const getCurrentX = () => currentColumn === 1 ? leftColumnX : rightColumnX;
  const getCurrentWidth = () => currentColumn === 1 && !isSecondPage ? contentWidth : columnWidth;

  const addTitle = (title: string, size: number = 16) => {
    doc.setFontSize(size);
    doc.setTextColor(primaryColor);
    doc.setFont('helvetica', 'bold');
    doc.text(title, getCurrentX(), yPosition);
    yPosition += size === 16 ? 12 : 8;
    
    // Add underline
    doc.setDrawColor(primaryColor);
    doc.setLineWidth(0.5);
    const titleWidth = doc.getTextWidth(title);
    doc.line(getCurrentX(), yPosition - 6, getCurrentX() + titleWidth, yPosition - 6);
    yPosition += 4;
  };

  const addText = (text: string, fontSize: number = 10, color: string = textColor, isBold: boolean = false, justify: boolean = false) => {
    doc.setFontSize(fontSize);
    doc.setTextColor(color);
    doc.setFont('helvetica', isBold ? 'bold' : 'normal');
    
    if (justify && text.includes('\n')) {
      // Handle text with line breaks - justify each paragraph separately
      const paragraphs = text.split('\n');
      paragraphs.forEach((paragraph, index) => {
        if (paragraph.trim()) {
          const lines = doc.splitTextToSize(paragraph.trim(), getCurrentWidth());
          lines.forEach((line: string, lineIndex: number) => {
            if (justify && lineIndex < lines.length - 1 && lines.length > 1) {
              // Justify line by distributing spaces
              const words = line.split(' ');
              if (words.length > 1) {
                const totalTextWidth = words.reduce((sum, word) => sum + doc.getTextWidth(word), 0);
                const totalSpaceNeeded = getCurrentWidth() - totalTextWidth;
                const spacePerGap = totalSpaceNeeded / (words.length - 1);
                
                let currentX = getCurrentX();
                words.forEach((word, wordIndex) => {
                  doc.text(word, currentX, yPosition);
                  if (wordIndex < words.length - 1) {
                    currentX += doc.getTextWidth(word) + spacePerGap;
                  }
                });
              } else {
                doc.text(line, getCurrentX(), yPosition);
              }
            } else {
              doc.text(line, getCurrentX(), yPosition);
            }
            yPosition += fontSize * 0.6;
          });
        }
        if (index < paragraphs.length - 1) yPosition += 0.25; // Space between paragraphs
      });
      yPosition += 4;
    } else {
      const lines = doc.splitTextToSize(text, getCurrentWidth());
      lines.forEach((line: string, lineIndex: number) => {
        if (justify && lineIndex < lines.length - 1 && lines.length > 1) {
          // Justify line by distributing spaces
          const words = line.split(' ');
          if (words.length > 1) {
            const totalTextWidth = words.reduce((sum, word) => sum + doc.getTextWidth(word), 0);
            const totalSpaceNeeded = getCurrentWidth() - totalTextWidth;
            const spacePerGap = totalSpaceNeeded / (words.length - 1);
            
            let currentX = getCurrentX();
            words.forEach((word, wordIndex) => {
              doc.text(word, currentX, yPosition);
              if (wordIndex < words.length - 1) {
                currentX += doc.getTextWidth(word) + spacePerGap;
              }
            });
          } else {
            doc.text(line, getCurrentX(), yPosition);
          }
        } else {
          doc.text(line, getCurrentX(), yPosition);
        }
        yPosition += fontSize * 0.6;
      });
      yPosition += lines.length > 4 ? 1 : 4;
    }
  };

  const addSubtitle = (text: string, fontSize: number = 10, color: string = lightTextColor) => {
    doc.setFontSize(fontSize);
    doc.setTextColor(color);
    doc.setFont('helvetica', 'normal');
    
    const lines = doc.splitTextToSize(text, getCurrentWidth());
    doc.text(lines, getCurrentX(), yPosition);
    yPosition += lines.length * fontSize * 0.6 + 2;
  };

  const addBulletPoint = (text: string, indent: number = 5) => {
    doc.setFontSize(10);
    doc.setTextColor(textColor);
    doc.setFont('helvetica', 'normal');
    doc.text('•', getCurrentX() + indent, yPosition);
    
    const lines = doc.splitTextToSize(text, getCurrentWidth() - indent - 5);
    doc.text(lines, getCurrentX() + indent + 8, yPosition);
    yPosition += lines.length * 6 + 2;
  };

  const checkPageBreak = (additionalSpace: number = 20) => {
    if (yPosition + additionalSpace > doc.internal.pageSize.height - 20) {
      if (!isSecondPage) {
        doc.addPage();
        yPosition = 20;
        isSecondPage = true;
        currentColumn = 1;
      } else if (currentColumn === 1) {
        // Switch to right column
        currentColumn = 2;
        yPosition = 20;
      } else {
        // Add new page and reset
        doc.addPage();
        yPosition = 20;
        currentColumn = 1;
      }
    }
  };

  // Header (always full width on first page)
  doc.setFontSize(24);
  doc.setTextColor(primaryColor);
  doc.setFont('helvetica', 'bold');
  doc.text(data.personalInfo.name, margin, yPosition);
  yPosition += 12; // Reduced from 18

  doc.setFontSize(14);
  doc.setTextColor(textColor);
  doc.setFont('helvetica', 'normal');
  doc.text(data.personalInfo.title, margin, yPosition);
  yPosition += 15; // Reduced from 20

  // Contact Information (always full width on first page)
  doc.setFontSize(10);
  doc.setTextColor(lightTextColor);
  const contactLabels = {
    email: 'Email:',
    phone: t('about.phone'),
    location: t('about.nationality'),
    languages: t('about.languages')
  };
  
  const contactInfo = [
    `${contactLabels.email} ${data.personalInfo.email}`,
    `${contactLabels.phone} ${data.personalInfo.phone}`,
    `${contactLabels.location} ${data.personalInfo.location}`,
    `${contactLabels.languages} ${data.personalInfo.languages}`
  ];
  
  contactInfo.forEach((info) => {
    doc.text(info, margin, yPosition);
    yPosition += 6; // Reduced from 8
  });
  yPosition += 8; // Reduced from 10

  // About Section
  addTitle(t('about.title'));
  addText(data.about, 10, textColor, false, true);
  yPosition += 2;

  // Professional Experience Section
  addTitle(t('experience.title'));

  // Both experiences on PAGE 1
  data.experience.forEach((exp, index) => {
    addText(exp.title, 12, textColor, true);
    yPosition -= 4;
    addSubtitle(`${exp.company} | ${exp.period}`);
    yPosition -= 1;
    addText(exp.description, 10, textColor, false, true);
    if (exp.skills.length > 0) {
      yPosition -= 3;
      addText(t('cv.technologies'), 10, textColor, true);
      yPosition -= 4;
      addText(exp.skills.join(', '), 10, lightTextColor);
    }
    if (index < data.experience.length - 1) yPosition += 5;
  });

  // PAGE 2: Education, Technical Skills, Additional Training
  doc.addPage();
  yPosition = 20;
  isSecondPage = true;
  currentColumn = 1;
  const educationSkillsStartY = yPosition;

  // Left Column: Education
  addTitle(t('education.educationSubtitle'));
  
  data.education.forEach((edu: { degree: string; institution: string; period: string }) => {
    addText(edu.degree, 11, textColor, true);
    yPosition -= 2;
    addText(edu.institution, 10, lightTextColor);
    yPosition -= 3;
    addText(edu.period, 10, lightTextColor);
    yPosition += 2;
  });

  // Additional Training in left column after Education
  yPosition += 2;
  addTitle(t('education.trainingSubtitle'));

  data.additionalTraining.forEach((training: { name: string; institution: string; date: string }) => {
    addText(training.institution, 10, textColor, true);
    yPosition -= 2;
    addBulletPoint(training.name);
    yPosition += 2;
  });

  // Right Column: Technical Skills
  currentColumn = 2;
  yPosition = educationSkillsStartY;

  addTitle(t('skills.title'));

  const skillSections = [
    { title: t('skills.backend'), skills: data.skills.backend },
    { title: t('skills.cloud'), skills: data.skills.cloud },
    { title: t('skills.databases'), skills: data.skills.databases },
    { title: t('skills.tools'), skills: data.skills.tools }
  ];

  skillSections.forEach((section) => {
    addText(`${section.title}`, 10, textColor, true);
    yPosition -= 2;
    addText(section.skills.join(', '), 10, lightTextColor);
    yPosition += 2;
  });


  // Footer
  const pageCount = doc.getNumberOfPages();
  for (let i = 1; i <= pageCount; i++) {
    doc.setPage(i);
    doc.setFontSize(8);
    doc.setTextColor(lightTextColor);
    doc.text(
      `${data.personalInfo.name} - CV | ${language === 'es' ? 'Página' : 'Page'} ${i}`,
      pageWidth / 2,
      doc.internal.pageSize.height - 10,
      { align: 'center' }
    );
  }

  return doc;
}

export function downloadCV(cvData: CVData, language: 'es' | 'en', t: (key: string) => string) {
  if (!cvData || !cvData.personalInfo) {
    console.error('CV data is not available yet');
    return;
  }
  
  const pdf = generatePDF(cvData, language, t);
  const fileName = `${cvData.personalInfo.name.replace(/\s+/g, '_')}_CV_${language.toUpperCase()}_${new Date().getFullYear()}.pdf`;
  pdf.save(fileName);
}