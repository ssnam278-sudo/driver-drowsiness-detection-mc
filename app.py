"""Browser demo for the driver-drowsiness temporal decision layer."""

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

from drowsiness_state import AlertLevel, Config, DrowsinessMonitor, EyeState


st.set_page_config(page_title="Driver Drowsiness Detection", page_icon="ðŸš—", layout="wide")

st.title("Driver Drowsiness Detection")
st.caption("Interactive browser demo of the temporal decision layer")

with st.sidebar:
    st.header("Scenario")
    scenario = st.selectbox("Choose a driving pattern", ["Alert driver", "One microsleep", "Three microsleeps"])
    seconds = st.slider("Simulation length (seconds)", 10, 90, 30)
    st.info("This web demo visualizes the decision layer. It is not a certified safety system.")


def build_script(name: str, duration: int):
    if name == "Alert driver":
        return [(EyeState.OPEN, float(duration))]
    if name == "One microsleep":
        return [(EyeState.OPEN, 5.0), (EyeState.CLOSED, 0.9),
                (EyeState.OPEN, max(0.0, duration - 5.9))]
    block = [(EyeState.OPEN, 5.0)]
    for _ in range(3):
        block.extend([(EyeState.CLOSED, 0.8), (EyeState.OPEN, 2.0)])
    block.append((EyeState.OPEN, max(0.0, duration - 13.4)))
    return block


if st.button("Run analysis", type="primary"):
    monitor = DrowsinessMonitor(Config())
    rows = []
    t = 0.0
    previous = None
    for eye, span in build_script(scenario, seconds):
        steps = max(1, int(span * 25))
        for _ in range(steps):
            state = monitor.update(t, eye, False)
            rows.append({
                "time": t,
                "level": state.level.name,
                "PERCLOS": state.perclos * 100,
                "microsleeps": state.microsleeps,
                "closure": state.current_closure_s,
            })
            if state.level is not previous:
                previous = state.level
            t += 1 / 25

    final = state
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Decision", final.level.name)
    c2.metric("PERCLOS", f"{final.perclos:.1%}" if final.perclos_valid else "n/a")
    c3.metric("Microsleeps", final.microsleeps)
    c4.metric("Longest closure", f"{final.longest_closure_s:.1f}s")

    st.subheader("Timeline")
    st.line_chart(rows, x="time", y=["PERCLOS", "closure"], height=320)
    st.dataframe(rows[-1], use_container_width=True)
else:
    st.markdown("Choose a scenario and click **Run analysis** to see how temporal signals become an alert.")

