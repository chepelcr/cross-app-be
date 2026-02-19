import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { sendContactEmail } from "./email.js";

export async function registerRoutes(app: Express): Promise<Server> {
  // Contact form endpoint
  app.post("/api/contact", async (req, res) => {
    try {
      const { name, email, subject, message } = req.body;
      
      // Validate required fields
      if (!name || !email || !subject || !message) {
        return res.status(400).json({ 
          message: "Todos los campos son requeridos" 
        });
      }
      
      // Email validation
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email)) {
        return res.status(400).json({ 
          message: "Formato de email inválido" 
        });
      }
      
      // Log the submission
      console.log("Contact form submission:", {
        name,
        email,
        subject,
        message,
        timestamp: new Date().toISOString(),
      });
      
      // Send email notification
      const emailResult = await sendContactEmail({ name, email, subject, message });
      
      if (!emailResult.success) {
        console.error("Failed to send email:", emailResult.error);
        return res.status(500).json({
          message: "Error al enviar el mensaje. Por favor intenta más tarde.",
          success: false
        });
      }
      
      res.json({ 
        message: "Mensaje enviado exitosamente. Te contactaré pronto.",
        success: true 
      });
    } catch (error) {
      console.error("Error processing contact form:", error);
      res.status(500).json({ 
        message: "Error interno del servidor. Por favor intenta más tarde." 
      });
    }
  });

  // CV download endpoint
  app.get("/api/download-cv", async (req, res) => {
    try {
      // In a real application, you would:
      // 1. Generate a PDF from the portfolio data
      // 2. Serve the PDF file
      // 3. Track download analytics
      
      console.log("CV download requested at:", new Date().toISOString());
      
      res.json({ 
        message: "CV download will be available soon",
        success: true 
      });
    } catch (error) {
      console.error("Error serving CV download:", error);
      res.status(500).json({ 
        message: "Error al descargar el CV. Por favor intenta más tarde." 
      });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}
