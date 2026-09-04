"""Text utilities."""

def clean(text):
    text = text.replace("\n", " ")
    return " ".join(text.split())

