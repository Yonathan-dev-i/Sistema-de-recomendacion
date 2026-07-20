import { Hero } from "@/components/landing/hero";
import { HowItWorks } from "@/components/landing/how-it-works";
import { TestMethods } from "@/components/landing/test-methods";
import { CareersExplorer } from "@/components/landing/careers-explorer";
import { Benefits } from "@/components/landing/benefits";
import { Faq } from "@/components/landing/faq";
import { Footer } from "@/components/footer";

export default function HomePage() {
  return (
    <>
      <main id="contenido">
        <Hero />
        <HowItWorks />
        <TestMethods />
        <CareersExplorer />
        <Benefits />
        <Faq />
      </main>
      <Footer />
    </>
  );
}
