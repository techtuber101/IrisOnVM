import { HeroVideoDialog } from "@/components/home/ui/hero-video-dialog";

export function HeroVideoSection() {
  return (
    <div id="video" className="relative px-6 mt-6">
      <div className="relative w-full max-w-2xl mx-auto shadow-lg rounded-xl overflow-hidden">
        <HeroVideoDialog
          className="block dark:hidden"
          animationStyle="from-center"
          videoSrc="https://www.youtube.com/embed/RBE-C-b86-Y?si=coming-soon-graphics"
          thumbnailSrc="/thumbnail-light.png"
          thumbnailAlt="Hero Video"
        />
        <HeroVideoDialog
          className="hidden dark:block"
          animationStyle="from-center"
          videoSrc="https://www.youtube.com/embed/RBE-C-b86-Y?si=coming-soon-graphics"
          thumbnailSrc="/thumbnail-dark.png"
          thumbnailAlt="Hero Video"
        />
      </div>
    </div>
  );
}
