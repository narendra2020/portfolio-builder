// Shared helpers for building/mutating the resumes.content JSON document.
// Shape is defined by the backend (resume_profile_mapper.py / resume_prompts.py) —
// every leaf item carries a stable id and a "source" provenance tag
// (mepage_import | upload_import | scratch | ai_generated | user_edited).

export function newId() {
  return (crypto.randomUUID ? crypto.randomUUID() : `id-${Date.now()}-${Math.random().toString(16).slice(2)}`);
}

export function emptyContent() {
  return {
    personal: {
      full_name: "", email: "", phone: "", city: "", country: "",
      linkedin_url: "", portfolio_url: "", github_url: "",
    },
    summary: { text: "", source: "scratch" },
    experience: [],
    projects: [],
    skills: { groups: [], source: "scratch" },
    education: [],
    certifications: [],
    achievements: [],
    additional_sections: [],
  };
}

export function newExperience() {
  return {
    id: newId(), title: "", employer: "", location: "",
    start_date: "", end_date: "", is_current: false, date_range: "",
    bullets: [], source: "user_edited",
  };
}

export function newBullet() {
  return { id: newId(), text: "", source: "user_edited" };
}

export function newProject() {
  return { id: newId(), title: "", description_bullets: [], tags: [], link_url: "", source: "user_edited" };
}

export function newEducation() {
  return {
    id: newId(), institution: "", degree: "", field: "",
    start_date: "", end_date: "", date_range: "", gpa: "", source: "user_edited",
  };
}

export function newCertification() {
  return { id: newId(), name: "", issuer: "", date: "", source: "user_edited" };
}

export function newAchievement() {
  return { id: newId(), text: "", source: "user_edited" };
}

export function newAdditionalSection() {
  return { id: newId(), heading: "", items: [], source: "user_edited" };
}

export function newSkillGroup() {
  return { title: "", skills: [] };
}

export const IMPROVE_FIELD_ACTIONS = [
  { key: "more_concise", label: "Make more concise" },
  { key: "more_senior", label: "Sound more senior" },
  { key: "stronger_verb", label: "Use a stronger action verb" },
  { key: "quantify_impact", label: "Quantify the impact" },
  { key: "fix_grammar", label: "Fix grammar & spelling" },
  { key: "simplify", label: "Simplify the language" },
  { key: "add_keywords", label: "Add relevant keywords" },
  { key: "expand", label: "Expand with more detail" },
];
