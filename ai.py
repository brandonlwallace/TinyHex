# AI module that uses the RLAI class for intelligent opponent behavior
# The RLAI learns and improves through self-play

from rl_ai import RLAI

# For backward compatibility, expose RLAI as the main AI class
SimpleAI = RLAI

# Stubs used for animation calls - replaced by real references in main.py
def screen_stub():
    return None

def stub_font():
    return None