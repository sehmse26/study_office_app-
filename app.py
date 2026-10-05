import os
import numpy as np
import pandas as pd
import streamlit as st
import portable   # the helper from the hotel app, loads the saved model

URL = "https://raw.githubusercontent.com/aaubs/ds-master/main/assignments/study-office/data/"
HERE = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(page_title="Study office: who to talk to", layout="wide")

# ---------- Load the model and the data (cached so the app stays fast) ----------
@st.cache_resource
def load_model():
    folder = os.path.join(HERE, "model")
    if not os.path.isdir(folder):      # no model folder, so the files are at the top level
        folder = HERE
    return portable.Model(folder)

@st.cache_data
def load_data():
    history = pd.read_csv(URL + "history_week6.csv")
    new = pd.read_csv(URL + "new_week6.csv")
    return history, new

model = load_model()
history, new = load_data()

# 2025 cohort = the students we check the rule on (we know who really left)
val = history[history["cohort"] == 2025].copy()
val["risk"] = model.predict_proba(val)

# 2026 students = this week's list
new = new.copy()
new["risk"] = model.predict_proba(new)

# ---------- The rule: talk to the N students with the highest risk ----------
st.title("🎓 Who should the study office talk to?")
n = st.sidebar.slider("Number of conversations", 10, 150, 40)
st.sidebar.write("The advisers can hold about 40 conversations at the end of week 6.")

def mistakes(df):
    """Count the three outcomes in plain words for a group of 2025 students."""
    reached = int((df["contacted"] & (df["left"] == 1)).sum())    # talked to, and would have left
    worried = int((df["contacted"] & (df["left"] == 0)).sum())    # talked to, but was fine
    missed = int((~df["contacted"] & (df["left"] == 1)).sum())    # not talked to, and left
    return reached, worried, missed

# who the rule would contact among the 2025 students
val["contacted"] = val["risk"].rank(ascending=False, method="first") <= n

tab1, tab2, tab3, tab4 = st.tabs(["This week's list", "Mistakes of the rule", "Per group", "What it costs"])

# ---------- Tab 1: this week's list ----------
with tab1:
    ranked = new.sort_values("risk", ascending=False).reset_index(drop=True)
    ranked.insert(0, "rank", ranked.index + 1)
    ranked.insert(1, "talk to", np.where(ranked["rank"] <= n, "✅ yes", ""))
    ranked["risk"] = ranked["risk"].round(2)
    st.write(f"The {n} students with the highest risk are marked. The list is a suggestion: an adviser decides.")
    cols = ["rank", "talk to", "student_id", "risk", "programme", "international",
            "submitted_share", "logins_total", "fees_owed"]
    st.dataframe(ranked[cols], use_container_width=True, hide_index=True)

# ---------- Tab 2: the mistakes on the 2025 cohort ----------
with tab2:
    reached, worried, missed = mistakes(val)
    st.subheader(f"If we had talked to {n} students in 2025")
    a, b, c = st.columns(3)
    a.metric("Reached in time", reached)
    b.metric("Worried for nothing", worried)
    c.metric("Missed", missed)
    st.write(f"Of the {n} students we talked to, **{reached}** were really at risk and **{worried}** were fine. "
             f"**{missed}** students who left were not on the list.")
    st.write(f"That means we reached **{reached / (reached + missed):.0%}** of the students who left.")

# ---------- Tab 3: per group ----------
with tab3:
    st.subheader("The same numbers for international and domestic students")
    rows = []
    for flag, label in [(1, "International"), (0, "Domestic")]:
        g = val[val["international"] == flag]
        r, w, m = mistakes(g)
        rows.append({"Group": label, "Students": len(g), "Left": r + m,
                     "Reached in time": r, "Worried for nothing": w, "Missed": m,
                     "Share of leavers reached": f"{r / (r + m):.0%}" if (r + m) > 0 else "-"})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.write("If one group's leavers are reached less often, the same rule treats the groups differently.")

# ---------- Tab 4: our own addition, the costs behind the rule ----------
with tab4:
    st.subheader("What the rule costs and saves (2025 cohort)")
    st.write("These numbers are assumptions. Change them to see how the value of the rule moves.")
    c1, c2, c3, c4 = st.columns(4)
    cost_talk = c1.number_input("A conversation (DKK)", value=500, step=100)
    cost_worry = c2.number_input("A student worried for nothing (DKK)", value=2000, step=500)
    cost_leave = c3.number_input("A student who leaves (DKK)", value=60000, step=5000)
    helps = c4.slider("Share kept by a conversation", 0.0, 1.0, 0.30)
    reached, worried, missed = mistakes(val)
    net = reached * helps * cost_leave - (reached + worried) * cost_talk - worried * cost_worry
    st.metric("Net value of the rule (DKK)", f"{net:,.0f}")
