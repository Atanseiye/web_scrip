import re

def clean_excel_string(s):
    if not isinstance(s, str):
        return s  # Return the value unchanged if it's not a string

    # Remove control characters (ASCII codes 0-31)
    cleaned_string = ''.join(c for c in s if ord(c) >= 32)

    # Remove special characters not allowed in Excel sheet names
    # These characters are: : / \ ? * [ ]
    cleaned_string = re.sub(r'[:/\\?\*\[\]]', '', cleaned_string)

    return cleaned_string

string = "Sheet/Name?With:Special*Characters[Not]Allowed"
print(clean_excel_string(string))
