(function () {
  const translations = {
    en: {
      language: "Language",
      title: "Student Registration",
      intro: "Please fill in your details. Our team will contact you to complete enrollment.",
      promo: "Come train with us! Free trial class - no experience needed.",
      name: "Full Name",
      email: "Email",
      phone: "Phone",
      address: "Address",
      sex: "Gender",
      birthday: "Date of Birth",
      location: "Location",
      minor: "I am a minor",
      guardianName: "Guardian Name",
      guardianEmail: "Guardian Email",
      guardianPhone: "Guardian Phone",
      notes: "Notes",
      newsletter: "I agree to receive news and communications",
      privacy: "I agree to the processing of my personal data",
      submit: "Submit Registration",
      contactTitle: "Contact Us",
      contactLead: "Ready to try Jiu-Jitsu? Sign up now for a free trial class - no experience needed!",
      followTitle: "Follow Us",
      ttLanguage: "Choose interface language",
      ttName: "Enter first and last name",
      ttEmail: "Enter a valid email address",
      ttPhone: "Optional contact phone number",
      ttAddress: "Street and house number",
      ttSex: "Select gender",
      ttBirthday: "Select date of birth",
      ttMinor: "Check if the student is under 18",
      ttGuardianName: "Required if the student is a minor",
      ttGuardianEmail: "Required if the student is a minor",
      ttGuardianPhone: "Optional guardian contact number",
      ttNotes: "Optional extra information",
      ttNewsletter: "Allow us to send updates",
      ttPrivacy: "Required to submit the form",
      ttSubmit: "Send registration data",
      valRequired: "Please fill out this field.",
      valEmail: "Please enter a valid email address.",
      valDate: "Please enter a valid date.",
      valNumber: "Please enter a valid number.",
      valLength: "The value is too long.",
      valMinorGuardianName: "Guardian name is required for minors.",
      valMinorGuardianEmail: "Guardian email is required for minors.",
      valPrivacyRequired: "You must accept data processing to continue.",
      errSave: "Registration could not be saved.",
      okSaved: "Registration received. We will contact you shortly.",
      errNetwork: "Network error while submitting registration.",
    },
    de: {
      language: "Sprache",
      title: "Schueler-Anmeldung",
      intro: "Bitte fuellen Sie Ihre Daten aus. Unser Team kontaktiert Sie fuer die finale Aufnahme.",
      promo: "Komm und trainiere mit uns! Kostenloses Probetraining - keine Vorkenntnisse noetig.",
      name: "Vollstaendiger Name",
      email: "E-Mail",
      phone: "Telefon",
      address: "Adresse",
      sex: "Geschlecht",
      birthday: "Geburtsdatum",
      location: "Standort",
      minor: "Ich bin minderjaehrig",
      guardianName: "Name des Erziehungsberechtigten",
      guardianEmail: "E-Mail des Erziehungsberechtigten",
      guardianPhone: "Telefon des Erziehungsberechtigten",
      notes: "Notizen",
      newsletter: "Ich moechte Neuigkeiten und Mitteilungen erhalten",
      privacy: "Ich stimme der Verarbeitung meiner personenbezogenen Daten zu",
      submit: "Anmeldung senden",
      contactTitle: "Kontakt",
      contactLead: "Bereit fuer Jiu-Jitsu? Melde dich jetzt fuer ein kostenloses Probetraining an - keine Vorkenntnisse noetig!",
      followTitle: "Folge uns",
      ttLanguage: "Sprache der Oberflaeche waehlen",
      ttName: "Vor- und Nachname eingeben",
      ttEmail: "Gueltige E-Mail-Adresse eingeben",
      ttPhone: "Optionale Telefonnummer",
      ttAddress: "Strasse und Hausnummer",
      ttSex: "Geschlecht auswaehlen",
      ttBirthday: "Geburtsdatum auswaehlen",
      ttMinor: "Aktivieren, wenn der Schueler unter 18 ist",
      ttGuardianName: "Erforderlich bei Minderjaehrigen",
      ttGuardianEmail: "Erforderlich bei Minderjaehrigen",
      ttGuardianPhone: "Optionale Telefonnummer des Erziehungsberechtigten",
      ttNotes: "Optionale Zusatzinformationen",
      ttNewsletter: "Neuigkeiten und Mitteilungen erlauben",
      ttPrivacy: "Erforderlich zum Absenden",
      ttSubmit: "Anmeldedaten senden",
      valRequired: "Bitte dieses Feld ausfuellen.",
      valEmail: "Bitte eine gueltige E-Mail-Adresse eingeben.",
      valDate: "Bitte ein gueltiges Datum eingeben.",
      valNumber: "Bitte eine gueltige Zahl eingeben.",
      valLength: "Der Wert ist zu lang.",
      valMinorGuardianName: "Name des Erziehungsberechtigten ist bei Minderjaehrigen erforderlich.",
      valMinorGuardianEmail: "E-Mail des Erziehungsberechtigten ist bei Minderjaehrigen erforderlich.",
      valPrivacyRequired: "Sie muessen der Datenverarbeitung zustimmen, um fortzufahren.",
      errSave: "Die Anmeldung konnte nicht gespeichert werden.",
      okSaved: "Anmeldung erhalten. Wir melden uns in Kuerze.",
      errNetwork: "Netzwerkfehler beim Senden der Anmeldung.",
    },
  };

  const form = document.getElementById("preRegForm");
  const message = document.getElementById("formMessage");
  const submitBtn = document.getElementById("submitBtn");
  const languageSwitch = document.getElementById("languageSwitch");
  const isMinor = document.getElementById("is_minor");
  const guardianFields = document.getElementById("guardianFields");
  const guardianName = document.getElementById("guardian_name");
  const guardianEmail = document.getElementById("guardian_email");
  let currentLang = "en";

  const apiBase = (window.__API_BASE_URL__ || "").replace(/\/+$/, "");
  const endpoint = apiBase ? `${apiBase}/public/pre-registrations` : "/public/pre-registrations";

  function setMessage(text, type) {
    message.textContent = text || "";
    message.className = `message${type ? ` ${type}` : ""}`;
  }

  function t(key) {
    const group = translations[currentLang] || translations.en;
    return group[key] || translations.en[key] || key;
  }

  function applyLanguage(lang) {
    currentLang = lang === "de" ? "de" : "en";
    document.documentElement.lang = currentLang;
    document.getElementById("languageLabel").textContent = t("language");
    document.getElementById("promoText").textContent = t("promo");
    document.getElementById("titleText").textContent = t("title");
    document.getElementById("introText").textContent = t("intro");
    document.getElementById("labelName").textContent = t("name");
    document.getElementById("labelEmail").textContent = t("email");
    document.getElementById("labelPhone").textContent = t("phone");
    document.getElementById("labelAddress").textContent = t("address");
    document.getElementById("labelSex").textContent = t("sex");
    document.getElementById("labelBirthday").textContent = t("birthday");
    document.getElementById("labelMinor").textContent = t("minor");
    document.getElementById("labelGuardianName").textContent = t("guardianName");
    document.getElementById("labelGuardianEmail").textContent = t("guardianEmail");
    document.getElementById("labelGuardianPhone").textContent = t("guardianPhone");
    document.getElementById("labelNotes").textContent = t("notes");
    document.getElementById("labelNewsletter").textContent = t("newsletter");
    document.getElementById("labelPrivacy").textContent = t("privacy");
    document.getElementById("submitBtn").textContent = t("submit");
    document.getElementById("contactTitle").textContent = t("contactTitle");
    document.getElementById("contactLead").textContent = t("contactLead");
    document.getElementById("followTitle").textContent = t("followTitle");
    document.getElementById("languageSwitch").title = t("ttLanguage");
    document.getElementById("name").title = t("ttName");
    document.getElementById("email").title = t("ttEmail");
    document.getElementById("phone").title = t("ttPhone");
    document.getElementById("address").title = t("ttAddress");
    document.getElementById("sex").title = t("ttSex");
    document.getElementById("birthday").title = t("ttBirthday");
    document.getElementById("is_minor").title = t("ttMinor");
    document.getElementById("guardian_name").title = t("ttGuardianName");
    document.getElementById("guardian_email").title = t("ttGuardianEmail");
    document.getElementById("guardian_phone").title = t("ttGuardianPhone");
    document.getElementById("notes").title = t("ttNotes");
    document.getElementById("newsletter_opt_in").title = t("ttNewsletter");
    document.getElementById("consent_privacy").title = t("ttPrivacy");
    document.getElementById("submitBtn").title = t("ttSubmit");
    languageSwitch.value = currentLang;
  }

  function onMinorToggle() {
    const minor = Boolean(isMinor.checked);
    guardianFields.classList.toggle("hidden", !minor);
    guardianName.required = minor;
    guardianEmail.required = minor;
  }

  function normalizeText(value) {
    const v = (value || "").trim();
    return v || null;
  }

  function clearValidationMessages() {
    const controls = form.querySelectorAll("input, select, textarea");
    controls.forEach(function (control) {
      control.setCustomValidity("");
    });
  }

  function setLocalizedValidity(control) {
    control.setCustomValidity("");
    const validity = control.validity;
    if (validity.valid) return;
    let messageText = t("valRequired");
    if (control.id === "guardian_name" && isMinor.checked && validity.valueMissing) {
      messageText = t("valMinorGuardianName");
    } else if (control.id === "guardian_email" && isMinor.checked && validity.valueMissing) {
      messageText = t("valMinorGuardianEmail");
    } else if (control.id === "consent_privacy" && validity.valueMissing) {
      messageText = t("valPrivacyRequired");
    } else if (validity.typeMismatch && control.type === "email") {
      messageText = t("valEmail");
    } else if (validity.badInput && control.type === "number") {
      messageText = t("valNumber");
    } else if (validity.badInput && control.type === "date") {
      messageText = t("valDate");
    } else if (validity.tooLong) {
      messageText = t("valLength");
    }
    control.setCustomValidity(messageText);
  }

  function applyValidationMessages() {
    const controls = form.querySelectorAll("input, select, textarea");
    controls.forEach(function (control) {
      setLocalizedValidity(control);
    });
  }

  function validateWithLocalizedMessages() {
    clearValidationMessages();
    applyValidationMessages();
    if (form.checkValidity()) return true;
    form.reportValidity();
    return false;
  }

  async function submitForm(event) {
    event.preventDefault();
    setMessage("", "");
    onMinorToggle();
    if (!validateWithLocalizedMessages()) {
      return;
    }

    submitBtn.disabled = true;
    const data = new FormData(form);
    const locationRaw = (data.get("location_id") || "1").toString().trim();
    const payload = {
      name: (data.get("name") || "").toString().trim(),
      email: (data.get("email") || "").toString().trim(),
      sex: (data.get("sex") || "M").toString().trim().toUpperCase(),
      phone: normalizeText(data.get("phone")),
      address: normalizeText(data.get("address")),
      birthday: normalizeText(data.get("birthday")),
      is_minor: isMinor.checked,
      guardian_name: normalizeText(data.get("guardian_name")),
      guardian_email: normalizeText(data.get("guardian_email")),
      guardian_phone: normalizeText(data.get("guardian_phone")),
      newsletter_opt_in: document.getElementById("newsletter_opt_in").checked,
      location_id: Number(locationRaw) || 1,
      notes: normalizeText(data.get("notes")),
      consent_privacy: document.getElementById("consent_privacy").checked,
      website: (data.get("website") || "").toString(),
    };

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const body = await response.json().catch(function () {
        return {};
      });
      if (!response.ok) {
        const detail = body && body.detail ? String(body.detail) : t("errSave");
        throw new Error(detail);
      }
      form.reset();
      onMinorToggle();
      setMessage(t("okSaved"), "success");
    } catch (error) {
      setMessage(
        error && error.message ? error.message : t("errNetwork"),
        "error"
      );
    } finally {
      submitBtn.disabled = false;
    }
  }

  languageSwitch.addEventListener("change", function (event) {
    applyLanguage(event.target.value);
    applyValidationMessages();
  });
  form.querySelectorAll("input, select, textarea").forEach(function (control) {
    control.addEventListener("input", function () {
      control.setCustomValidity("");
    });
    control.addEventListener("invalid", function () {
      setLocalizedValidity(control);
    });
  });
  isMinor.addEventListener("change", onMinorToggle);
  form.addEventListener("submit", submitForm);
  applyLanguage("de");
  onMinorToggle();
})();
