import { useEffect } from "react";
import { useAuth } from "./AuthProvider";
import { dirForLocale, resolveLocale } from "../lib/i18n";

export default function RuntimePreferences() {
  const { user } = useAuth();
  useEffect(() => {
    const locale = resolveLocale(user?.profile.locale ?? navigator.language);
    document.documentElement.lang = locale;
    document.documentElement.dir = dirForLocale(locale);
    document.body.classList.toggle("nur-rtl", document.documentElement.dir === "rtl");
    document.body.classList.toggle("nur-sound-enabled", user?.profile.sound_enabled === true);
  }, [user?.profile.locale, user?.profile.sound_enabled]);
  return null;
}
