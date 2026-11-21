# Agent Studio

Turn one expert's knowledge into a talking agent with a face that answers in English and French, and only ever says
what that expert approved. Producers build the agent (face, voice, sources, topics); the invited expert approves each
answer; a published version gets a public page anyone can talk to. Built on [Anvil](https://anvil.works) as native
Anvil Forms (Python + HTML templates, a layout, custom components, RepeatingPanels).

Made as a working prototype of the "Agent Studio" feature Addanapp pitched (agent builder with expert approval). The
demo content is three invented guides to Montréal restaurants; the studio works the same for any subject.

- **App repo:** github.com/arkulinskis/pitch-rxchainge (branch `master`). Anvil pulls `master`.
- **Live:** not published yet

## What it does

**Visitors**
- Landing page with a live demo face that asks and answers its own sample questions (English, then French) with the
  expert's "Approved by" stamp; pick between three demo guides.
- Public agent page `#talk/<slug>`: the agent's live face (blinks, glances at the pointer, lip-syncs), English /
  Français switch, optional voice (the browser's own speech), suggested questions, the conversation, and who approved
  the answers. Unknown questions get "I don't know yet, passed on to <expert>"; refused subjects get a polite no.
- **"Why this answer?"** under every agent reply (EN/FR): the matched approved topic, who approved it and when, the
  version it answers from (or "preview"), the sources it was drafted from, and the match strength with the shared
  words; refusals name the refused-subject rule, unknowns say they were logged for the expert.
- **Presenter mode** `#demo/<slug>` (2026-11-20): a scripted walk-through for showing the app to someone. Pick a demo
  guide; a step card (Say / Do / the scripted question) beside the live chat; "Run this step" asks it in the step's
  language; Back / Next / arrow keys; steps: meet the guide, approved answer + receipt, French, refused subject,
  unknown question logged as a gap, behind the scenes. Questions are checked server-side against the live version
  (Talk.get_demo_script), so each step gets the reply it promises. Linked from the landing page and the studio.

**Producers (signed in)**
- **Studio** (`#studio`): my agents, agents I review as the invited expert, and the three demo agents (look-only,
  with "Make my own copy"). New agent from a template (its face, sources and topics come along as drafts) or blank.
- **Agent editor** (`#agent/<id>/<tab>`):
  - *Overview*: identity (name, subject, tagline and greeting in English | French side by side, tone), "Getting it
    live" checklist with progress, the expert (invite / change / remove by email), questions asked and unanswered.
  - *Face & voice*: the avatar studio. Live preview, skin, hair style and colour, eyes, brows, glasses, accessory,
    top, background, Shuffle, voice speed and pitch, "Say hello" / "Dis bonjour", undo, save.
  - *Knowledge*: sources (paste or upload .txt/.md; language detected), scope in both languages, refused subjects.
  - *Topics*: every question + answer in both languages with its status (draft, in review, changes asked, approved),
    filter, the topic editor (EN | FR columns, "Draft from sources" per language naming the sources used, keywords,
    save, send for review, approve, ask for changes with a note, delete), and "Asked, not answered" (repeats grouped
    with a count) with "Make it a topic" / "Dismiss".
  - *Try it*: the chat answering from the topics approved right now (before publishing), and which topic matched.
  - *Trust* (2026-11-20): **coverage** (share of public questions answered with a verdict: under 10% unanswered good,
    over 20% gaps; unanswered EN vs FR; topics missing French; approved but unpublished; waiting for the expert) and
    **unanswered themes** (open gaps clustered by shared words, most asked first, "Write a topic" resolves the whole
    theme); the **audit trail** (every create, edit, back-to-draft, send, approve, changes asked + note, delete, source
    added/removed, expert change, publish, rollback, offline; who and when; filter; Show all; Download CSV).
    The topic editor shows that topic's own history.
  - *Publish*: live version + link (copy / open), publish a new version with a note, version history with one-click
    "Make live" rollback, take offline.
- **Review** (`#review`): the expert's queue, English and French side by side, approve or ask for changes in place.

**Rules that keep the expert in charge**
- Only approved topics reach the public agent, and only from a published version (a frozen snapshot).
- Editing an approved answer sends it back to draft. Approval needs both languages.
- Once an expert is invited, only they can approve; with no expert the owner approves, marked "owner, no expert yet".
- Experts edit and approve but can't publish or delete; viewers (demo agents) only look.

**The brain** (`server_code/Engine.py`, no AI service, no key): language guess, accent-free tokens with EN+FR stop
words and a small stemmer, topic matching by weighted word overlap, refused-subject check, greeting detection, and
drafting by picking the source sentences that fit the question in the agent's tone.

**Admin**: the template's overview (people, agents made by people, feedback), users, demo data on/off.

## Setting it up in Anvil (once)

1. Anvil editor: **Create app → Clone from GitHub**, paste `https://github.com/arkulinskis/pitch-rxchainge`.
2. Check the **Users** service (email + password, Continue with Google, sign-up on).
3. Accept the **Schema Mismatch** alert with **"The schema of the source code is correct"**.
4. **App Secrets**: create `admin_emails` = your email (never written in the code). Run it, sign in with **Continue with
   Google** using that email (it becomes the admin), then **Publish**.
5. Admin status report (users, rows, errors): `/_/api/admin/status` while signed in as an admin.

<!-- libraries:start -->
## Libraries and outside services

What this project uses besides its own code. Generated by `APP_MAKER/tools/libraries.py`; to change it, edit `APP_MAKER/libraries/catalog.py` and re-run the script.

| Name | How it gets in | Used here for |
|---|---|---|
| [Google Fonts](https://fonts.google.com) | Loaded from a CDN | Figtree, Newsreader |

**Built into the browser:** Speech synthesis, localStorage, Clipboard.

**Anvil platform:** Anvil, Anvil Data Tables, Anvil Email, Anvil JS bridge (anvil.js), Anvil Secrets, Anvil Users, Anvil Google service, Anvil HTTP, Anvil timezones (anvil.tz), Anvil Media.

**Build and test tools (not shipped):** axe-core, Node.js, Headless Chrome (DevTools Protocol), PyYAML.

<!-- libraries:end -->

## Working on it

See `.claude/skills/pitchrxchainge/SKILL.md`. In short:

```
python tools/check.py                    # Anvil's validator, JS syntax, asset hashes, server tests -> ALL CHECKS PASSED
python -I tools/ui_test.py               # the real app in the Anvil App Server (Docker) driven by headless Chrome
python -I tools/ui_test.py --shots DIR   # + screenshots of every page (desktop/phone, light/dark, guest/member)
git push origin master                   # deploy
```

## Project layout

```
client_code/    startup.py, router.py, state.py, auth.py, legal.py, face.py (face engine wrapper)
                Layouts/Shell; Pages/ Landing Studio Agent Review Talk Auth Profile Admin
                Tabs/ Overview Look Knowledge Topics Try Publish (the editor's tabs)
                Components/ Face Chat HeroDemo; Items/ AgentCard TemplateCard TopicRow GapRow SourceRow RefuseChip
                Pick CheckStep VersionRow ReviewRow Message Suggest GuidePick GuideCard (+ NavLink FeedbackRow UserRow)
                Dialogs/ NewAgent TopicEditor AddSource ExpertDialog PublishDialog
server_code/    Agents.py (studio, editor data, roles), Topics.py (topics, review, sources, gaps), Versions.py
                (publish, rollback), Talk.py (public page, answering), Engine.py (matching + drafting),
                DemoContent.py (the three guides = templates), DemoData.py, + template modules
theme/assets/   as-face.js (the face engine), app.css, icons.css (generated), app-kit.js, theme.css, icon.svg + PNGs
tools/          check.py, assets.py, ui_test.py + ui/ (flow, phone, admin, a11y, design, seed), testing/test_server.py
```
