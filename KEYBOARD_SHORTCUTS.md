# ⌨️ Keyboard Shortcuts Quick Reference

## Global Shortcuts (Work anywhere, even when overlay is hidden)

| Shortcut | Action | Use Case |
|----------|--------|----------|
| **Ctrl+Shift+H** | Hide/Show overlay | Toggle visibility instantly |
| **Ctrl+Shift+P** | Pause/Resume listening | Pause during casual chat |
| **Ctrl+Shift+C** | Clear transcript | Start fresh for new question |
| **Ctrl+Shift+↑** | Increase font size | Make text larger (8-16px) |
| **Ctrl+Shift+↓** | Decrease font size | Make text smaller (8-16px) |
| **Ctrl+Shift+→** | Increase opacity | Make overlay more visible |
| **Ctrl+Shift+←** | Decrease opacity | Make overlay more transparent |
| **Ctrl+Shift+Q** | Emergency hide | Instant invisibility + stop all |

---

## When to Use Each Shortcut

### During Active Interview

**`Ctrl+Shift+P` (Pause/Resume)**
- Before: Casual introductions, non-technical chat
- After: Question answered, waiting for feedback
- Why: Saves processing power, reduces false positives

**`Ctrl+Shift+H` (Hide/Show)**
- When: Doing whiteboard work, drawing diagrams
- When: Screen sharing and overlay feels distracting
- Why: Keeps UI accessible but invisible

**`Ctrl+Shift+C` (Clear Transcript)**
- When: Moving to next question
- When: Topic change (behavioral → technical)
- Why: Cleans slate for new context

### Emergency Situations

**`Ctrl+Shift+Q` (Emergency Hide)**
- Cat jumps on keyboard
- Interviewer asks to share screen unexpectedly
- Need to disable everything instantly
- Why: Full shutdown, no traces

### Customization

**Font Size (`Ctrl+Shift+↑` / `↓`)**
- Adjust for your monitor size
- Larger for 4K displays
- Smaller for compact views
- Range: 8-16px

**Opacity (`Ctrl+Shift+→` / `←`)**
- Increase: Easier to read (darker background)
- Decrease: More stealthy (lighter background)
- Range: 10%-98%

---

## Shortcut Combos (Pro Tips)

### Quick Hide & Resume
```
1. Ctrl+Shift+Q  (emergency hide)
2. Wait for safe moment
3. Ctrl+Shift+H  (show again)
4. Ctrl+Shift+P  (resume listening)
```

### Clear & Refocus
```
1. Ctrl+Shift+C  (clear transcript)
2. Ctrl+Shift+P  (pause briefly)
3. Ctrl+Shift+P  (resume for new question)
```

### Optimize Visibility
```
1. Ctrl+Shift+← (decrease opacity) × 3-5
2. Ctrl+Shift+↑ (increase font) × 2
3. Result: Transparent overlay, readable text
```

---

## Memory Aids

**Think of it as layers:**
- **H** = Hide (visibility layer)
- **P** = Pause (processing layer)
- **C** = Clear (data layer)
- **Q** = Quit (everything layer)

**Arrow keys:**
- **↑/↓** = Size (vertical thinking)
- **←/→** = Opacity (horizontal transparency)

---

## Troubleshooting

**Shortcuts not working?**
1. Make sure app is running (check system tray)
2. Overlay window must exist (even if hidden)
3. No conflicts with other apps
4. Windows shortcuts have priority

**Want to remap shortcuts?**
Edit `frontend/main.py`, method `_setup_shortcuts()`:
```python
# Change from Ctrl+Shift+H to Ctrl+Alt+H
hide_shortcut = QShortcut(QKeySequence("Ctrl+Alt+H"), self.overlay)
```

---

## Practice Exercise

Before your interview, practice this sequence:

1. Start app → `python run.py`
2. Hide overlay → `Ctrl+Shift+H`
3. Show overlay → `Ctrl+Shift+H`
4. Pause listening → `Ctrl+Shift+P`
5. Resume listening → `Ctrl+Shift+P`
6. Clear transcript → `Ctrl+Shift+C`
7. Decrease opacity → `Ctrl+Shift+←` (×3)
8. Emergency hide → `Ctrl+Shift+Q`

**Goal**: Execute all shortcuts without looking at keyboard!

---

## Advanced: Custom Shortcuts

Want to add your own? Here's the template:

```python
# In frontend/main.py, _setup_shortcuts() method

# Custom: Ctrl+Shift+S - Save current answer
save_shortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self.overlay)
save_shortcut.activated.connect(self._save_answer)

def _save_answer(self):
    """Save current answer to file."""
    # Your implementation here
    pass
```

---

## Platform Differences

**Windows** (Current)
- All shortcuts work as documented
- Uses Windows API for stealth mode

**Mac** (Future support)
- Replace `Ctrl` with `Cmd`
- Adjust for macOS display affinity

**Linux** (Future support)
- Replace `Ctrl` with `Super` or keep as is
- May need X11/Wayland-specific stealth

---

## Summary

**Essential shortcuts to memorize:**
1. `Ctrl+Shift+H` - Your panic button (hide)
2. `Ctrl+Shift+P` - Your control (pause)
3. `Ctrl+Shift+Q` - Your nuclear option (emergency)

**Everything else is optional customization!**

Print this page or keep it on a second monitor during your first few practice runs.

---

**Pro tip**: Practice shortcuts while watching a YouTube coding interview. Get muscle memory before the real thing!

Good luck! 🚀
