# Think9 Hub Demo Script (2–3 Minutes Walkthrough)

This walkthrough demonstrates the complete lifecycle of the **Think9 Intelligence Hub** platform: from initial brand manager inquiry to agent run, human-in-the-loop review, and historical lookup.

---

## Part 1: Dashboard and Setup (30 Seconds)
1. **Action**: Open the dashboard at `http://localhost:5173`.
2. **Narration**: 
   > "Welcome to the Think9 Intelligence Hub. We are managing 30+ distinct consumer brands centrally. On our dashboard, you can see our statistics, active brands, and the live log of all resolved issues and institutional decisions."
3. **Action**: Point to the active brands count (3) and the recent resolved issue table showing historical actions.

---

## Part 2: Ask Think9 & Agent Inquiries (60 Seconds)
1. **Action**: Click on the **Ask Think9** tab. Select **AURA** and **Hydrating Face Wash** from the dropdown selectors.
2. **Action**: Input the query: 
   > `"Why has customer satisfaction declined for AURA Face Wash over the last 30 days and what should we do?"`
   Click **Investigate**.
3. **Narration**:
   > "Let's assume a brand manager for AURA wants to find out why ratings dropped recently. As we hit 'Investigate', the multi-agent system triggers. The Router maps the query context. The Research Agent crawls reviews and RAG documentation. The Analysis Agent identifies the dominant issue from the actual feedback and calculates the change in negative-feedback rate between the current and previous 30-day periods. The Memory Agent searches the historical records of other brands, and the Recommendation Agent consolidates all evidence."
4. **Action**: Point to the **Agent Activities** logs showing completed states, the dynamic trend comparison data, and the evidence strength indicator displaying the calculated score and reasons.

---

## Part 3: Human-In-The-Loop Panel (30 Seconds)
1. **Action**: Click on **Review Action Recommendations**.
2. **Narration**:
   > "The AI generates a highly detailed mitigation plan based on CapTech flip-top caps and torque limits, but we maintain absolute human control. In our HITL panel, a reviewer can modify the action plan directly. Let's enter our name and click 'APPROVE DECISION'."
3. **Action**: Enter `"Sarah Jenkins (VP Quality)"` as reviewer, keep or tweak recommendations, and click **APPROVE DECISION**. An alert popup will confirm the decision has been logged.

---

## Part 4: Proof of Institutional Memory (30 Seconds)
1. **Action**: Navigate to the **Decision Memory** tab.
2. **Action**: Type `"leakage"` or `"packaging"` in the search bar.
3. **Narration**:
   > "To prove the system learns, let's look up similar incidents. We can search for 'leakage'. Instantly, we retrieve our newly stored AURA packaging leakage decision along with the historic VIVA shaker bottle leakage incident resolved months ago. The system has officially retained this institutional knowledge, and the decision is now stored as institutional memory and can be reused in future investigations."
4. **Action**: Conclude the walkthrough showing both records in the table.
