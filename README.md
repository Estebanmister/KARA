# KARA

#### Customizable Capable Neural (Transformer based) Chatbots

Features: Vision, Memories ( Disabled by default, two different methods will be implemented), Personalities and animated characters!

##### Includes an example discord bot interface, join our discord to play around with it!

Also please join the discord if you need help setting things up: https://discord.gg/vK4RjZWbkU

The code is still being actively and quickly modified to fix bugs and make it user friendly. Give me about a week.
You probably do not need all of the files present here, all the scripts starting with load_ are for 
different transformer types.

configs and mesh_transformers are not needed if you are not using load_gptj, which uses a local TPU

API keys and urls are set in environmental variables.

It even generates a little animated avatar as a GIF!


#### Kara's structure:
    Core class: Easy to use interface for a transformer endpoint
        load_gpt3, load_gpt_forefront, load_gptj, load_gptj_new, load_gptneox
    
    Kara class: Chatbot itself
    
    VisualCore class: Easy to use interface for caption generators
        load_OFA load_VITCloud load_VIT
        
    Vidi class: For now just redirects inputs to a VisualCore class
    
    SALIERI (Syl): Handles generating the animated avatar, works with Parser to do so
    
    Parser: do not touch this, I have yet to clean this code
    
    VITserver.ipynb: Server for load_VITCloud

## A lot more will be written here about the theory and principles!!
