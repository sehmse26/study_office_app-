@st.cache_resource
def load_model():
    folder = os.path.join(HERE, "model")
    if not os.path.isdir(folder):
        folder = HERE
    return portable.Model(folder)
