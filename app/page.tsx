import type { Metadata } from "next";
import HomeContent from "./home-content";

export const metadata: Metadata = {
  title: "SmartCampus AI : l’orientation universitaire en une conversation",
  description:
    "Discutez avec l’assistant en français, en tunisien ou en Arabizi pour choisir votre formation à l’IIT ou à l’ISB, puis préinscrivez-vous.",
};

export default function Home() {
  return <HomeContent />;
}
