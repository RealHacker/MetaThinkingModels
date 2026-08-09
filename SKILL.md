---
name: thinking-models
description: Apply a mental/thinking model from the bundled models library to solve problems more creatively and effectively. Use this skill whenever a problem requires lateral thinking or creative solutions, such as when the user asks you to "think outside the box", "get creative", "find another angle", "reframe this", or when the standard, obvious approach feels stuck, inadequate, or unoriginal. If the problem is stubborn, ambiguous, or would benefit from a fresh mental framework before jumping into code or a plan, this skill should trigger — even if the user never explicitly mentions "thinking model".
---

# Thinking Models

This skill exists because the most obvious answer is rarely the best one. The repo ships a library of distilled thinking models (mental models, heuristics, and problem-solving frameworks) in the `models/` folder. Each file describes one model — what it is, why it works, and worked examples. When you're asked to solve a problem that rewards creativity or a fresh angle, your job is to find the right model, absorb its method, and then solve the problem through that lens instead of defaulting to your usual approach.

## Trigger

Activate this skill when the problem needs lateral thinking or creative problem-solving. Concrete signals:

- The user asks you to be creative, think differently, brainstorm, or break out of a rut.
- The standard/linear approach is blocked, expensive, or already failed.
- The problem is ambiguous or poorly defined and would benefit from reframing before solving.
- A single "obvious" answer exists but feels too easy, too conventional, or like it's missing something.

If the task is a straightforward, well-specified operation (e.g., "write a function that sorts this list", "format this document"), do NOT use this skill.

## Workflow

The process is exactly two steps, in order. Do not skip step 1.

### Step 1: List the models and pick a candidate

List all model files in the `models/` directory (relative to this skill's folder). Use the Glob tool with the pattern `models/*.txt`, or `ls models/` if Glob is unavailable.

Scan the file names (each name encodes the model, e.g., `lateral_thinking`, `first_principle`, `inversion`, `five_whys`) and decide whether one of them maps usefully onto the problem at hand.

Selection heuristics:

- Match the model name to the *kind* of thinking the problem rewards, not to the problem's topic. `first_principle` is about stripping assumptions to fundamentals; `inversion` is about asking "how would I make this fail?"; `five_whys` is for root-cause digging; `lateral_thinking` is for deliberately breaking the obvious pattern.
- If several models could help, choose the single most relevant one first. You may read a second if the first doesn't click, but avoid skimming the whole library.
- If no model name plausibly applies, stop and solve normally — do not force a model onto a problem that doesn't fit.

### Step 2: Read the model file and apply it

Read the chosen file, e.g. `models/lateral_thinking.txt`.

Each model file uses this structure:

- `<define>` — the method itself: what the model is and how to think with it.
- `<example>` — one or more worked examples showing the model applied to real problems.

Internalize the method from `<define>`, then solve the original problem by applying that method. Explicitly walk through it: state the model you're using, restate the problem through its lens, then produce your solution. Applying the model faithfully matters more than polish — if the model says to invert the goal, challenge an assumption, or reduce to first principles, actually do that and show your work.

## Output

Deliver your solution to the user's problem as normal (answer, code, plan, or artifact), but make it clear that it was derived from a thinking model: name the model you used and briefly note how it shaped the approach. This helps the user understand why the answer looks different from the obvious one.

## Examples

**Example 1 — creative angle on a growth problem**
Problem: "How can we get more users for our app?"
Model: `first_principle` → strip away "we need better marketing" and ask what irreducible need the app serves and who benefits most; the answer may reframe the entire go-to-market instead of boosting ad spend.

**Example 2 — stuck design decision**
Problem: "We keep disagreeing on the pricing model."
Model: `inversion` → ask "how would we guarantee this pricing fails?" and reverse each failure mode into a requirement; the disagreement usually dissolves once the failure conditions are explicit.
