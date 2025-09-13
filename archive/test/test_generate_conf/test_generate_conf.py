from pathlib import Path
import sys
ROOT=Path(__file__).parent.parent.parent.parent
sys.path.append(str(ROOT))

from SVSv2 import generate_execonf

def main():

    conf_path=Path(__file__).parent/"conf.yml"
    outpath=Path(__file__).parent/"execonf.yml"

    generate_execonf(
        conf_path=conf_path,
        outpath=outpath
    )

if __name__=="__main__":
    main()