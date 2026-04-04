import { Syne, DM_Mono } from "next/font/google";
import "./globals.css";

const syne = Syne({
  subsets: ["latin"],
  variable: "--font-syne",
  weight: ["400", "600", "700", "800"],
});

const dmMono = DM_Mono({
  subsets: ["latin"],
  variable: "--font-dm-mono",
  weight: ["300", "400", "500"],
});

export const metadata = {
  title: "WhyNotHireMe — AI Resume Analyzer",
  description: "Find out exactly why you didn't get hired.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body
        className={`${syne.variable} ${dmMono.variable}`}
        style={{
          fontFamily: "var(--font-syne), sans-serif",
          background: "var(--bg)",
          color: "var(--text)",
          minHeight: "100vh",
        }}
      >
        {children}
      </body>
    </html>
  );
}