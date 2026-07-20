import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "1.5rem",
      screens: { "2xl": "1280px" },
    },
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        border: "hsl(var(--border))",
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // Guinda/vino institucional (UNA Puno) — color primario.
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
          50: "#fbf1f2",
          100: "#f4dde0",
          200: "#e6b8bf",
          300: "#d38b96",
          400: "#bc5c6c",
          500: "#a5303f",
          600: "#8a2734",
          700: "#6e1f2b",
          800: "#571a22",
          900: "#3d1017",
        },
        // Dorado institucional — color de acento.
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
          300: "#e6cc72",
          400: "#d8b94a",
          500: "#c9a227",
          600: "#a8841e",
          700: "#846719",
        },
        // DEFAULT se usa para badges sólidos (fondo de color + texto blanco).
        // La variante 700 (Fase 9d) es más oscura y se usa como *texto* sobre
        // fondos tintados claros (ej. "bg-success/15 text-success-700"):
        // DEFAULT sobre blanco da ~3.3:1 (no cumple WCAG AA 4.5:1 para texto
        // normal), mientras que 700 da >5:1 en ambos casos.
        success: { DEFAULT: "#16a34a", foreground: "#ffffff", 700: "#15803d" },
        warning: { DEFAULT: "#d97706", foreground: "#ffffff", 700: "#b45309" },
        danger: { DEFAULT: "#dc2626", foreground: "#ffffff" },
        ring: "hsl(var(--ring))",
      },
      borderRadius: {
        lg: "0.75rem",
        xl: "1rem",
        "2xl": "1.25rem",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "var(--font-sans)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 40px -8px hsl(var(--primary) / 0.45)",
        "glow-accent": "0 0 40px -8px hsl(var(--accent) / 0.45)",
      },
      backgroundImage: {
        "gradient-brand": "linear-gradient(90deg, hsl(226 100% 68%), hsl(258 90% 64%))",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-10px)" },
        },
        "float-slow": {
          "0%, 100%": { transform: "translateY(0px) rotate(0deg)" },
          "50%": { transform: "translateY(-16px) rotate(1deg)" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        float: "float 6s ease-in-out infinite",
        "float-slow": "float-slow 9s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;