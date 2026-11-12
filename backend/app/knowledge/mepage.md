# MePage product knowledge (source of truth for the website assistant)

Edit this file to change what the assistant knows. It is loaded at startup and sent to the
model as its only source of facts. Keep it factual and short. Anything not written here, the
assistant will say it does not know.

Items marked [VERIFY] were taken from the codebase or earlier planning and should be confirmed
by the team before relying on them.

## About MePage
- MePage is a product of Mindora AI. Website: https://mepage.in. App: https://app.mepage.in
- Support: care@mepage.in, phone +91 96672 73354.
- MePage has three products: the Portfolio Website Builder, the AI Resume Builder and the
  QR Code Store Builder.
- Users sign up with an Indian mobile number and a one-time password (OTP). [VERIFY: the
  portfolio signup is India-only]

## Product 1: Portfolio Website Builder (https://app.mepage.in)
- Creates a professional, mobile-friendly personal portfolio website without coding.
- Flow: sign up, add your details (you can upload a resume to pre-fill them, using AI), choose a
  template, arrange the layout, then publish.
- Published sites live on a MePage subdomain, for example name.mepage.in.
- Suitable for students, professionals, freelancers, entrepreneurs, creators and job seekers.
- Sites are responsive (desktop, tablet and mobile) and built with search-friendly structure.
- You can edit your profile and republish whenever your work changes.

### Pricing and trial for the portfolio builder [VERIFY]
- Every new account starts with a 30-day free trial.
- When the trial ends, a published site is taken down until the account is upgraded.
- The upgrade costs Rs 999 for 1 year and keeps the site published. The website shows this as
  "starting from about Rs 84 per month, billed Rs 999 per year". There is no monthly payment: it
  is one yearly payment of Rs 999.
- Payment can be made by card, UPI, netbanking or wallet through Razorpay, or by UPI with a
  manual review by the MePage team.
- Custom domains: the website mentions connecting a personal domain, but the app does not show
  a custom domain feature yet. The assistant must not promise it. Direct users to
  care@mepage.in to ask about availability.

### AI Assistant add-on for portfolios [VERIFY]
- Portfolio owners can add an AI chat assistant to their published site. Visitors, for example
  hiring managers, can ask it questions about the owner's skills, projects and experience.
- It answers only from the owner's profile and the question and answer pairs the owner writes.
- It is a paid add-on at Rs 499. [VERIFY: duration and what it is billed against]

## Product 2: AI Resume Builder (https://mepage.in/ai-resume-builder)
- A guided workspace that combines resume sections with AI writing support.
- Sections: Personal, Summary, Experience, Projects, Skills, Education, Certifications,
  Achievements, Additional.
- AI helps draft summaries, experience and project descriptions, and can tailor content to a
  job description.
- ATS guidance and a score are provided as advice only. No resume builder can guarantee that a
  resume passes an applicant tracking system or leads to a shortlist.
- Resumes can be exported as a PDF. Users should always check the file, including that the text
  is selectable.
- AI suggestions can be edited. Users must check accuracy before sending a resume.
- Whether the resume builder is free, limited or paid is not confirmed. Direct pricing
  questions to the app or care@mepage.in. Do not claim it is free or unlimited.

## Product 3: QR Code Store Builder (https://mepage.in/qr-code, app: https://qr.mepage.in)
- Turns a photo of a menu, catalogue or price list into a mobile store with a branded QR code.
- Flow: upload photos, AI extracts items, categories and prices, the owner reviews them, picks
  a design and branding, then publishes.
- A price is accepted from the photo only if that exact number appears in the printed text.
  Anything unclear is flagged and must be reviewed before publishing.
- Published stores live at yourstore.mepage.in. The address is locked after the first publish so
  that printed QR codes keep working.
- Store addresses use lowercase letters, digits and single hyphens, 3 to 63 characters, and must
  be unique across QR stores and portfolio sites. Some names are reserved.
- Five storefront designs: Menu Classic (restaurants, grocery), Cafe Cards (cafes, bakeries,
  salons), Boutique Elegant (wedding, fashion, jewellery), Auto Showroom (automobile,
  electronics) and Retail Grid (any shop).
- Customers scan the QR code, browse on their phone with no app, and send an enquiry to the
  store's WhatsApp, either for one item or a list. The customer presses Send themselves. The
  store never claims an order was placed and there is no online payment in the store.
- QR codes can be downloaded as PNG or SVG, as a card or plain, for screen or print.
- Activity counters show the last 30 days of taps that opened WhatsApp. No IP addresses,
  cookies or message text are stored.
- Source photos are deleted 30 days after the first publish.
- Up to 1000 items per catalogue. Only Indian (+91) numbers can be used to log in. The business
  WhatsApp number can be international after a one-time code check.
- Plans: Free allows 5 catalogue updates per calendar month after the first publish (Asia/Kolkata
  time, resets on the 1st). Edits before the first publish are never counted. A Pro plan removes
  the limit. The Pro price is not confirmed. Direct price questions to the app or care@mepage.in.
- Custom domains for stores are planned but not available yet.

## Policies and honesty rules
- Terms and Privacy pages exist at https://mepage.in/terms and https://mepage.in/privacy but
  are drafts. Do not summarise legal terms. Direct legal questions to care@mepage.in.
- MePage does not guarantee jobs, interviews, shortlists, search ranking or inclusion in AI
  search results.
- The testimonials on the website are samples, not real customer reviews.

## Things the assistant cannot do
- It cannot access any user's account, orders, payments or published site.
- It cannot change settings, issue refunds, reset passwords or verify payments.
- For account, billing or payment problems, direct the user to care@mepage.in or the phone number.
