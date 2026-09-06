import "./globals.css";
import type { Metadata } from "next";
export const metadata: Metadata = {title:"PDF Question Agent", description:"Ask questions from your PDF using an image."};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>}