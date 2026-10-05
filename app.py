     @st.cache_resource
   def load_model():
       folder = os.path.join(HERE, "model")
       if not os.path.isdir(folder):      # no model folder, so the files are at the top level
           folder = HERE
       return portable.Model(folder)
