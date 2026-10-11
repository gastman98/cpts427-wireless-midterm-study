"""CPTS 427 Wireless Midterm Study App.

Run:  python study_app.py
Modes: Flashcards, Multiple Choice, Matching, Acronyms.
Questions live in questions.json (edit/add freely).
"""
import json
import random
import tkinter as tk
from pathlib import Path
from tkinter import ttk

DATA_FILE = Path(__file__).with_name("questions.json")
REVIEW_SOURCES = {"Blooket", "Jeopardy"}

BG = "#1e1f26"
PANEL = "#2a2c36"
FG = "#e8e8ee"
MUTED = "#9aa0b4"
ACCENT = "#5b8def"
GOOD = "#3fb27f"
BAD = "#e05a5a"
FONT = ("Segoe UI", 12)
FONT_B = ("Segoe UI", 12, "bold")
FONT_L = ("Segoe UI", 16, "bold")


def load_data():
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def build_flashcards(data):
    cards = []
    for t in data["terms"]:
        cards.append({**t})
    for q in data["mc"]:
        cards.append({
            "source": q["source"], "topic": q["topic"],
            "front": q["q"],
            "back": q["options"][q["answer"]] + "\n\n" + q.get("explain", ""),
        })
    for m in data["matching"]:
        for left, right in m["pairs"]:
            cards.append({
                "source": m["source"], "topic": m["topic"],
                "front": f"{left}\n\n({m['prompt']})",
                "back": right,
            })
    return cards


class Btn(tk.Button):
    def __init__(self, master, text, cmd, color=ACCENT, **kw):
        super().__init__(master, text=text, command=cmd, bg=color, fg="white",
                         activebackground=color, activeforeground="white",
                         relief="flat", font=FONT_B, padx=14, pady=6,
                         cursor="hand2", takefocus=0, **kw)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CPTS 427 Wireless Midterm Study")
        self.geometry("1000x720")
        self.minsize(820, 600)
        self.configure(bg=BG)

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=PANEL, background=PANEL,
                        foreground=FG, arrowcolor=FG)
        style.map("TCombobox",
                  fieldbackground=[("readonly", PANEL)], background=[("readonly", PANEL)],
                  foreground=[("readonly", FG)], selectbackground=[("readonly", PANEL)],
                  selectforeground=[("readonly", FG)])
        self.option_add("*TCombobox*Listbox.background", PANEL)
        self.option_add("*TCombobox*Listbox.foreground", FG)
        self.option_add("*TCombobox*Listbox.font", FONT)

        self.data = load_data()
        self.cards_all = build_flashcards(self.data)
        topics = sorted({x["topic"] for x in self.data["mc"] + self.data["matching"] + self.data["terms"]})

        self.topic_var = tk.StringVar(value="All topics")
        self.source_var = tk.StringVar(value="All sources")

        # Top bar
        bar = tk.Frame(self, bg=PANEL)
        bar.pack(fill="x")
        for label, fn in [("Home", self.show_home), ("Flashcards", self.start_flashcards),
                          ("Multiple Choice", self.start_mc), ("Matching", self.start_matching),
                          ("Acronyms", self.show_acronyms)]:
            Btn(bar, label, fn).pack(side="left", padx=4, pady=8)
        ttk.Combobox(bar, textvariable=self.source_var, state="readonly", width=22,
                     values=["All sources", "Review docs only", "Lecture supplements only"]
                     ).pack(side="right", padx=8)
        ttk.Combobox(bar, textvariable=self.topic_var, state="readonly", width=30,
                     values=["All topics"] + topics).pack(side="right", padx=4)
        tk.Label(bar, text="Filter:", bg=PANEL, fg=MUTED, font=FONT).pack(side="right")

        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill="both", expand=True, padx=24, pady=16)
        self.bind_all("<Key>", self._on_key)
        self.key_handler = None
        self.mc_new = self.start_mc
        self.show_home()

    # ---------- helpers ----------
    def _on_key(self, e):
        if self.key_handler and not isinstance(e.widget, (ttk.Combobox, tk.Entry, ttk.Entry)):
            self.key_handler(e)

    def clear(self):
        self.key_handler = None
        for w in self.body.winfo_children():
            w.destroy()

    def filt(self, items):
        t, s = self.topic_var.get(), self.source_var.get()
        out = []
        for x in items:
            if t != "All topics" and x["topic"] != t:
                continue
            if s == "Review docs only" and x["source"] not in REVIEW_SOURCES:
                continue
            if s == "Lecture supplements only" and x["source"] in REVIEW_SOURCES:
                continue
            out.append(x)
        return out

    def label(self, parent, text, font=FONT, fg=FG, bg=BG, **kw):
        return tk.Label(parent, text=text, font=font, fg=fg, bg=bg,
                        wraplength=900, justify="left", **kw)

    def tag(self, parent, item):
        self.label(parent, f"{item['topic']}  ·  {item['source']}", fg=MUTED).pack(anchor="w")

    def empty(self):
        self.label(self.body, "No items match the current filter.", font=FONT_L).pack(pady=40)

    # ---------- home ----------
    def show_home(self):
        self.clear()
        d = self.data
        self.label(self.body, "CPTS 427 Wireless Midterm Study", font=("Segoe UI", 22, "bold")).pack(anchor="w")
        rev_mc = sum(q["source"] in REVIEW_SOURCES for q in d["mc"])
        rev_m = sum(m["source"] in REVIEW_SOURCES for m in d["matching"])
        stats = (f"{len(d['mc'])} multiple-choice questions ({rev_mc} from review docs)\n"
                 f"{len(d['matching'])} matching sets ({rev_m} from review docs)\n"
                 f"{len(self.cards_all)} flashcards\n"
                 f"{len(d.get('acronyms', []))} acronyms")
        self.label(self.body, stats, fg=MUTED).pack(anchor="w", pady=(6, 18))
        tips = ("Suggested flow:\n"
                "  1. Flashcards with filter 'Review docs only' (these are what's on the exam).\n"
                "  2. Multiple Choice and Matching on review docs.\n"
                "  3. Repeat with 'All sources' for deeper coverage.\n\n"
                "Keys:  Flashcards: Space = flip, ←/→ = prev/next, K = got it, R = review again\n"
                "       Multiple Choice: 1-4 = answer, Enter = next\n"
                "       Matching: Enter = check / next\n"
                "       Acronyms: type to search; drill as flashcards or a quiz")
        self.label(self.body, tips, font=("Consolas", 11)).pack(anchor="w")

    # ---------- flashcards ----------
    def start_flashcards(self, deck=None):
        self.clear()
        self.fc_deck = deck if deck is not None else self.filt(self.cards_all)
        if not self.fc_deck:
            return self.empty()
        self.fc_i, self.fc_flipped, self.fc_missed = 0, False, []

        top = tk.Frame(self.body, bg=BG)
        top.pack(fill="x")
        self.fc_prog = self.label(top, "", fg=MUTED)
        self.fc_prog.pack(side="left")
        Btn(top, "Shuffle", self.fc_shuffle, color=PANEL).pack(side="right")

        self.fc_card = tk.Frame(self.body, bg=PANEL, cursor="hand2")
        self.fc_card.pack(fill="both", expand=True, pady=14)
        self.fc_side = tk.Label(self.fc_card, font=FONT_B, bg=PANEL, fg=MUTED)
        self.fc_side.pack(anchor="nw", padx=16, pady=10)
        self.fc_text = tk.Label(self.fc_card, font=("Segoe UI", 16), bg=PANEL, fg=FG,
                                wraplength=820, justify="center")
        self.fc_text.pack(expand=True, padx=24, pady=24)
        for w in (self.fc_card, self.fc_text, self.fc_side):
            w.bind("<Button-1>", lambda e: self.fc_flip())

        ctl = tk.Frame(self.body, bg=BG)
        ctl.pack()
        Btn(ctl, "◀ Prev", lambda: self.fc_move(-1), color=PANEL).pack(side="left", padx=4)
        Btn(ctl, "Flip", self.fc_flip).pack(side="left", padx=4)
        Btn(ctl, "Review again", self.fc_miss, color=BAD).pack(side="left", padx=4)
        Btn(ctl, "Got it", self.fc_got, color=GOOD).pack(side="left", padx=4)
        Btn(ctl, "Next ▶", lambda: self.fc_move(1), color=PANEL).pack(side="left", padx=4)

        def keys(e):
            k = e.keysym.lower()
            if k == "space": self.fc_flip()
            elif k == "right": self.fc_move(1)
            elif k == "left": self.fc_move(-1)
            elif k == "k": self.fc_got()
            elif k == "r": self.fc_miss()
        self.key_handler = keys
        self.fc_render()

    def fc_render(self):
        c = self.fc_deck[self.fc_i]
        self.fc_prog.config(text=f"Card {self.fc_i + 1}/{len(self.fc_deck)}   ·   "
                                 f"{c['topic']} · {c['source']}   ·   marked for review: {len(self.fc_missed)}")
        self.fc_side.config(text="ANSWER" if self.fc_flipped else "QUESTION / TERM",
                            fg=GOOD if self.fc_flipped else MUTED)
        self.fc_text.config(text=c["back"] if self.fc_flipped else c["front"])

    def fc_flip(self):
        self.fc_flipped = not self.fc_flipped
        self.fc_render()

    def fc_move(self, d):
        self.fc_i = (self.fc_i + d) % len(self.fc_deck)
        self.fc_flipped = False
        self.fc_render()

    def fc_shuffle(self):
        random.shuffle(self.fc_deck)
        self.fc_i, self.fc_flipped = 0, False
        self.fc_render()

    def fc_got(self):
        c = self.fc_deck[self.fc_i]
        if c in self.fc_missed:
            self.fc_missed.remove(c)
        self.fc_advance()

    def fc_miss(self):
        c = self.fc_deck[self.fc_i]
        if c not in self.fc_missed:
            self.fc_missed.append(c)
        self.fc_advance()

    def fc_advance(self):
        if self.fc_i == len(self.fc_deck) - 1:
            self.fc_done()
        else:
            self.fc_move(1)

    def fc_done(self):
        missed = list(self.fc_missed)
        self.clear()
        self.label(self.body, "Deck complete", font=FONT_L).pack(anchor="w")
        self.label(self.body, f"{len(missed)} card(s) marked 'review again'.", fg=MUTED).pack(anchor="w", pady=8)
        row = tk.Frame(self.body, bg=BG)
        row.pack(anchor="w", pady=10)
        if missed:
            Btn(row, "Study missed cards", lambda: self.start_flashcards(missed), color=BAD).pack(side="left", padx=4)
        Btn(row, "Restart full deck", self.start_flashcards).pack(side="left", padx=4)

    # ---------- multiple choice ----------
    def start_mc(self, pool=None):
        self.clear()
        qs = list(pool) if pool is not None else self.filt(self.data["mc"])
        if not qs:
            return self.empty()
        random.shuffle(qs)
        self.mc_qs, self.mc_i, self.mc_score, self.mc_wrong = qs, 0, 0, []
        if pool is None:
            self.mc_new = self.start_mc
        self.mc_render()

    def mc_render(self):
        self.clear()
        q = self.mc_qs[self.mc_i]
        self.mc_answered = False
        self.label(self.body, f"Question {self.mc_i + 1}/{len(self.mc_qs)}    Score: {self.mc_score}",
                   fg=MUTED).pack(anchor="w")
        self.tag(self.body, q)
        self.label(self.body, q["q"], font=FONT_L).pack(anchor="w", pady=(10, 14))

        order = list(range(len(q["options"])))
        random.shuffle(order)
        self.mc_order = order
        self.mc_btns = []
        for n, idx in enumerate(order):
            b = tk.Button(self.body, text=f"{n + 1}.  {q['options'][idx]}", anchor="w", justify="left",
                          wraplength=880, font=FONT, bg=PANEL, fg=FG, activebackground=PANEL,
                          activeforeground=FG, relief="flat", padx=14, pady=10, cursor="hand2", takefocus=0,
                          command=lambda n=n: self.mc_pick(n))
            b.pack(fill="x", pady=4)
            self.mc_btns.append(b)

        self.mc_feedback = self.label(self.body, "")
        self.mc_feedback.pack(anchor="w", pady=10)
        self.mc_next = Btn(self.body, "Next ▶", self.mc_advance)

        def keys(e):
            if e.char in "123456" and e.char and not self.mc_answered:
                n = int(e.char) - 1
                if n < len(self.mc_btns):
                    self.mc_pick(n)
            elif e.keysym == "Return" and self.mc_answered:
                self.mc_advance()
        self.key_handler = keys

    def mc_pick(self, n):
        if self.mc_answered:
            return
        self.mc_answered = True
        q = self.mc_qs[self.mc_i]
        chosen = self.mc_order[n]
        correct_n = self.mc_order.index(q["answer"])
        for b in self.mc_btns:
            b.config(state="disabled", disabledforeground=FG)
        self.mc_btns[correct_n].config(bg=GOOD)
        if chosen == q["answer"]:
            self.mc_score += 1
            self.mc_feedback.config(text="✓ Correct.  " + q.get("explain", ""), fg=GOOD)
        else:
            self.mc_btns[n].config(bg=BAD)
            self.mc_wrong.append(q)
            self.mc_feedback.config(text="✗ Incorrect.  " + q.get("explain", ""), fg=BAD)
        self.mc_next.pack(anchor="e")

    def mc_advance(self):
        self.mc_i += 1
        if self.mc_i < len(self.mc_qs):
            self.mc_render()
        else:
            self.mc_done()

    def mc_done(self):
        wrong = list(self.mc_wrong)
        total = len(self.mc_qs)
        self.clear()
        pct = round(100 * self.mc_score / total)
        self.label(self.body, f"Score: {self.mc_score}/{total}  ({pct}%)", font=FONT_L).pack(anchor="w")
        row = tk.Frame(self.body, bg=BG)
        row.pack(anchor="w", pady=10)
        if wrong:
            Btn(row, f"Retry {len(wrong)} missed", lambda: self.start_mc(wrong), color=BAD).pack(side="left", padx=4)
        Btn(row, "New round", self.mc_new).pack(side="left", padx=4)
        if wrong:
            self.label(self.body, "Missed:", font=FONT_B).pack(anchor="w", pady=(12, 4))
            box = tk.Text(self.body, bg=PANEL, fg=FG, font=FONT, wrap="word", relief="flat", height=18)
            for q in wrong:
                box.insert("end", f"• {q['q']}\n   → {q['options'][q['answer']]}\n\n")
            box.config(state="disabled")
            box.pack(fill="both", expand=True)

    # ---------- matching ----------
    def start_matching(self, pool=None):
        self.clear()
        sets = list(pool) if pool is not None else self.filt(self.data["matching"])
        if not sets:
            return self.empty()
        random.shuffle(sets)
        self.mt_sets, self.mt_i, self.mt_right, self.mt_total, self.mt_wrong = sets, 0, 0, 0, []
        self.mt_render()

    def mt_render(self):
        self.clear()
        m = self.mt_sets[self.mt_i]
        self.mt_checked = False
        self.label(self.body, f"Set {self.mt_i + 1}/{len(self.mt_sets)}    "
                              f"Pairs correct so far: {self.mt_right}/{self.mt_total}", fg=MUTED).pack(anchor="w")
        self.tag(self.body, m)
        self.label(self.body, m["prompt"], font=FONT_L).pack(anchor="w", pady=(10, 14))

        rights = [r for _, r in m["pairs"]]
        letters = "ABCDEFGHIJ"
        shuffled = rights[:]
        random.shuffle(shuffled)
        self.mt_key = {r: letters[i] for i, r in enumerate(shuffled)}

        bank = tk.Frame(self.body, bg=PANEL)
        bank.pack(fill="x", pady=(0, 12))
        for i, r in enumerate(shuffled):
            tk.Label(bank, text=f"{letters[i]}.  {r}", font=FONT, bg=PANEL, fg=FG,
                     wraplength=880, justify="left").pack(anchor="w", padx=12, pady=3)

        grid = tk.Frame(self.body, bg=BG)
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1)
        self.mt_rows = []
        choices = [letters[i] for i in range(len(shuffled))]
        for i, (left, right) in enumerate(m["pairs"]):
            tk.Label(grid, text=left, font=FONT_B, bg=BG, fg=FG, wraplength=560,
                     justify="left").grid(row=i, column=0, sticky="w", pady=5)
            var = tk.StringVar()
            cb = ttk.Combobox(grid, textvariable=var, values=choices, state="readonly", width=5, font=FONT)
            cb.grid(row=i, column=1, padx=10)
            res = tk.Label(grid, text="", font=FONT, bg=BG, wraplength=320, justify="left")
            res.grid(row=i, column=2, sticky="w")
            self.mt_rows.append((var, right, res))

        self.mt_btn = Btn(self.body, "Check", self.mt_check)
        self.mt_btn.pack(anchor="e", pady=12)
        self.key_handler = lambda e: self.mt_btn.invoke() if e.keysym == "Return" else None

    def mt_check(self):
        if self.mt_checked:
            return self.mt_advance()
        self.mt_checked = True
        n_ok = 0
        for var, right, res in self.mt_rows:
            want = self.mt_key[right]
            if var.get() == want:
                n_ok += 1
                res.config(text="✓", fg=GOOD)
            else:
                res.config(text=f"✗  {want}: {right}", fg=BAD)
        self.mt_right += n_ok
        self.mt_total += len(self.mt_rows)
        if n_ok < len(self.mt_rows):
            self.mt_wrong.append(self.mt_sets[self.mt_i])
        self.mt_btn.config(text="Next ▶")

    def mt_advance(self):
        self.mt_i += 1
        if self.mt_i < len(self.mt_sets):
            self.mt_render()
        else:
            self.mt_done()

    def mt_done(self):
        wrong = list(self.mt_wrong)
        self.clear()
        pct = round(100 * self.mt_right / max(self.mt_total, 1))
        self.label(self.body, f"Pairs correct: {self.mt_right}/{self.mt_total}  ({pct}%)", font=FONT_L).pack(anchor="w")
        row = tk.Frame(self.body, bg=BG)
        row.pack(anchor="w", pady=10)
        if wrong:
            Btn(row, f"Retry {len(wrong)} imperfect set(s)", lambda: self.start_matching(wrong),
                color=BAD).pack(side="left", padx=4)
        Btn(row, "New round", self.start_matching).pack(side="left", padx=4)

    # ---------- acronyms ----------
    def acr_list(self):
        t = self.topic_var.get()
        items = [x for x in self.data.get("acronyms", []) if t == "All topics" or x["topic"] == t]
        return sorted(items, key=lambda x: x["a"].lower())

    def show_acronyms(self):
        self.clear()
        items = self.acr_list()
        if not items:
            return self.empty()
        head = tk.Frame(self.body, bg=BG)
        head.pack(fill="x")
        self.label(head, f"Acronyms ({len(items)})", font=FONT_L).pack(side="left")
        Btn(head, "Quiz me", lambda: self.acr_quiz(items)).pack(side="right", padx=4)
        Btn(head, "Drill as flashcards", lambda: self.acr_flash(items), color=GOOD).pack(side="right", padx=4)

        q = tk.StringVar()
        row = tk.Frame(self.body, bg=BG)
        row.pack(fill="x", pady=10)
        self.label(row, "Search:", fg=MUTED).pack(side="left")
        ent = tk.Entry(row, textvariable=q, font=FONT, bg=PANEL, fg=FG, insertbackground=FG,
                       relief="flat", width=40)
        ent.pack(side="left", padx=8, ipady=4)
        ent.focus_set()

        frame = tk.Frame(self.body, bg=PANEL)
        frame.pack(fill="both", expand=True)
        sb = tk.Scrollbar(frame)
        sb.pack(side="right", fill="y")
        box = tk.Text(frame, bg=PANEL, fg=FG, font=FONT, wrap="word", relief="flat",
                      padx=14, pady=10, yscrollcommand=sb.set, cursor="arrow")
        box.pack(fill="both", expand=True)
        sb.config(command=box.yview)
        box.tag_config("a", font=("Consolas", 13, "bold"), foreground=ACCENT)
        box.tag_config("n", foreground=MUTED)

        def render(*_):
            term = q.get().strip().lower()
            box.config(state="normal")
            box.delete("1.0", "end")
            shown = 0
            for x in items:
                hay = f"{x['a']} {x['full']} {x.get('note', '')}".lower()
                if term and term not in hay:
                    continue
                shown += 1
                box.insert("end", f"{x['a']:<9}", "a")
                box.insert("end", f" {x['full']}")
                if x.get("note"):
                    box.insert("end", f"  ({x['note']})", "n")
                box.insert("end", "\n")
            if not shown:
                box.insert("end", "No matches.", "n")
            box.config(state="disabled")
        q.trace_add("write", render)
        render()

    def acr_flash(self, items):
        deck = [{"source": "Acronyms", "topic": x["topic"], "front": x["a"],
                 "back": x["full"] + (f"\n\n({x['note']})" if x.get("note") else "")} for x in items]
        random.shuffle(deck)
        self.start_flashcards(deck)

    def acr_quiz(self, items):
        pool_all = self.data["acronyms"]
        qs = []
        for x in items:
            wrong = random.sample([y["full"] for y in pool_all if y["full"] != x["full"]], 3)
            qs.append({"source": "Acronyms", "topic": x["topic"],
                       "q": f"What does {x['a']} stand for?",
                       "options": [x["full"]] + wrong, "answer": 0,
                       "explain": f"{x['a']} = {x['full']}." + (f" {x['note']}." if x.get("note") else "")})
        self.mc_new = lambda: self.acr_quiz(items)
        self.start_mc(qs)


if __name__ == "__main__":
    App().mainloop()
