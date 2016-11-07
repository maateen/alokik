# Alokik

Extract answer choices from scanned jpg bubble forms.

The mother project, [omr](https://github.com/GregoryCMiller/omr), is a tool that Greg Miller started 3 years ago, written in Python2. Unfortunately, he was not able to maintain his code because of lack of time. Perhaps, he used some backdated things which arent's compatible with present anymore.

## Graphical User Interface

```
python3 alokik.py
```

## Command Line

```
python3 alokik-cli.py [options] imagedir
```

#### imagedir

Input image directory (front side). Lowest numbered image identifies the key.

#### --backdir=BACKDIR

Optional back side image directory

#### --form=FORM

Set the form string (default and only supported="882E")

#### --help

Show this help message and exit

### Output

#### validation images

Answer bubble means and reference box fits drawn over each input image.

#### results.xlsx

#### summary

Image path, name box image, and total score for each test.

#### questioninfo

Answer choice counts by question. Key excluded.

#### scoring

Answer choice matches key (0/1). Same indices as choices. Score is 0 if key is -1.

#### choices

Answer choice matrix. Tests in rows and questions in columns. 0-4=A-E, -1=n/a.