#!/bin/bash

# Defaults
DEF_FORCE="n"
#DEF_METHOD="cli" - nice with --method-kwargs "commands=['show ip interface']"
# but output is JSON
DEF_METHOD="_send_command"

# mocked data dir
MDDIR="mocked_data"
# command output dir
CODIR="command_output"
# config
CMDIN="./$(basename $0 .sh ).cfg"

GETOPTS=":hu:p:ft:m:i:l:v:d:"                                                   
function usage() {                                                           
    MSG="usage: $(basename $0) [-h] -u USERNAME -p PASSWORD [-f]\n"
    MSG+="          [-m METHOD] -i INTERFACE -l LLDP_INTERFACE\n"
    MSG+="          -t TYPE -v VENDOR -d DEVICE [SINGLE_COMMAND]\n"
    MSG+="\n"
    MSG+="   This utility helps to get output of commands from device.\n"
    MSG+="     Set of commands can be configured in '$CMDIN'\n"
    MSG+="     Command output is saved to '$CODIR/DEVICE_TYPE/command_out.txt'\n"
    MSG+="     and by default is not to be overwriten.\n"
    MSG+="\n"
    MSG+="   There is not any IP, MAC or names obfuscation or anonymizations!\n"
    MSG+="   Before using as a unit test files it is recommendet to protect\n"
    MSG+="   your privacy information yourself by editing output files\n"
    MSG+="   in '$CODIR/DEVICE_TYPE/command_out.txt'!\n"
    MSG+="\n"
    MSG+="   -h           - this help\n"
    MSG+="   -u USERNAME  - login username (or env DEVUSERNAME)\n"
    MSG+="   -p PASSWORD  - login password (or env DEVPASSWORD)\n"
    MSG+="   -f           - overwrite already downloaded output files\n"
    MSG+="   -t TYPE      - device type\n"
    MSG+="   -m METHOD    - what method sends command to device (def '$DEF_METHOD')\n"
    MSG+="   -i INTERFACE - interface for deailed info (see '$CMDIN')\n"
    MSG+="   -l INTERFACE - interface for deailed lldp info (see '$CMDIN')\n"
    MSG+="   -v VENDOR    - vendor napalm driver\n"
    MSG+="   -d DEVICE    - device to connect\n"
                                                                             
    [[ -n $@ ]] && echo -e "\n###  $@  ###\n" >&2

    echo -e "$MSG" >&2                                                          
    exit 127                                                                 
}                                                                            


# Parse options
# No run without options
if ( ! getopts $GETOPTS opt); then # CLI bez options
    usage "Options needed !!!"
fi
OPTIND=1 # reset index

# Preset defaults
FORCE="$DEF_FORCE"
METHOD="$DEF_METHOD"

while getopts $GETOPTS opt; do
    #echo $opt;

    case "$opt" in
        'u')
            DEVUSERNAME=$OPTARG ;;

        'p')
            DEVPASSWORD=$OPTARG ;;

        't')
            TYPE=$OPTARG ;;

        'i')
            INTERFACE=$OPTARG ;;

        'l')
            LLDPINTERFACE=$OPTARG ;;

        'v')
            VENDOR=$OPTARG ;;

        'm')
            METHOD=$OPTARG ;;

        'd')
            DEVICE=$OPTARG ;;

        'f')
            FORCE='y' ;;

        'h')
            usage ;;

        ':')
            usage "Parameter '-$OPTARG' needs value."
            ;;

        '?'|*)
            usage "Unknown parameter '-$OPTARG' ."
            ;;
    esac
done


# read commands from file
[ -f "$CMDIN" ] || usage "File '$CMDIN' does not exists."
[ -r "$CMDIN" ] || usage "Can not read file '$CMDIN'."

[ -z "$INTERFACE" ]     && usage "Parameter -i needed"
[ -z "$LLDPINTERFACE" ] && usage "Parameter -l needed"

. "${CMDIN}"

# Get possible last arg and set it as only command
shift $(($OPTIND - 1))
[ -z "$1" ] || COMMANDS=("$1")

[ -z "$DEVUSERNAME" ]   && usage "Parameter -u needed"
[ -z "$DEVPASSWORD" ]   && usage "Parameter -p needed"
[ -z "$TYPE" ]          && usage "Parameter -t needed"
[ -z "$VENDOR" ]        && usage "Parameter -v needed"
[ -z "$DEVICE" ]        && usage "Parameter -d needed"

# ensure directory structure exists
[ -d "$CODIR" ] || usage "Output directory '$CODIR' does not exist."
[ -w "$CODIR" ] || usage "Output directory '$CODIR' is not writeable."

mkdir -p "$CODIR/$TYPE" || usage "Can not make directory '$CODIR/$TYPE'"
[ -w "$CODIR/$TYPE" ] || usage "Output directory '$CODIR/$TYPE' is not writeable."

echo "########## Generate output for type $TYPE ##########"
# lets get commands outputs
OLDIFS="$IFS"
IFS=$'\t\n'
for CMD in ${COMMANDS[@]}
do
    IFS="$OLDIFS"

    CMDSTR=${CMD// /_}
    CMDSTR=${CMDSTR//-/_}
    CMDSTR=${CMDSTR/\\/_}
    CMDSTR=${CMDSTR/./_}
    CMDSTR=${CMDSTR////_}
    CMDFILE="$CODIR/$TYPE/${CMDSTR}.txt"

    # skip already fetched command outputs
    if [ -f "$CMDFILE" -a "$FORCE" = "n" ]; then
        echo "###### Skiping '$CMD'. File '$CMDFILE' exists"
        continue
    fi

    echo "## Fetching '$CMD' to '$CMDSTR.txt'"
    # --debug
    set -x 
    echo -e "$(napalm --debug --user "$DEVUSERNAME" --password "$DEVPASSWORD" --vendor "$VENDOR" "$DEVICE" call --method-kwargs "command='$CMD'" "$METHOD" | sed 's/^"//;s/"$//;s/\\"/"/g')" > "$CMDFILE"
    set +x
done

echo "#### Preparing obfuscate script"
echo "## IP addresses"
IPs=$(cat "$CODIR/$TYPE/"*.txt \
    | sed -rn 's/.*[^0-9\.](([0-9]{1,3}\.){3}[0-9]{1,3})[^0-9\.].*/\1/gp' \
    | sort \
    | uniq
)
echo $IPs

for a in $IPs
do
    oa=${a}
    oa=${oa//1/3}
    oa=${oa//2/3}
    oa=${oa//4/3}
    oa=${oa//5/3}
    oa=${oa//6/7}
    oa=${oa//8/7}
    oa=${oa//9/7}

    oa=" -e s/$a/$oa/g "

    oIPs="$oIPs$oa "
done

echo "## MAC addresses"
MACs=$(cat "$CODIR/$TYPE/"*.txt \
    | sed -rn -e 's/.*[^0-9\.:a-f-](([[:xdigit:]]{2}[:.-]?){5}[[:xdigit:]]{2})[^0-9\.:a-f-].*/\1/gp' \
    | sort \
    | uniq 
)
echo $MACs

for m in $MACs
do
    om=${m}
    om=${om//1/2}
    om=${om//3/2}
    om=${om//6/2}
    om=${om//8/2}
    om=${om//b/2}
    om=${om//e/2}
    om=${om//4/a}
    om=${om//5/a}
    om=${om//7/a}
    om=${om//9/a}
    om=${om//c/a}
    om=${om//d/a}

    om=" -e s/$m/$om/g "

    oMACs="$oMACs$om "
done

echo "## Obfuscate IPs and MACs"
echo oIPS=$oIPs
echo oMACs=$oMACs
set -x 
sed -r -iOBF $oMACs $oIPs "$CODIR/$TYPE/"*.txt
set +x

echo "## Obfuscate strings from OBFUSCATE config variable"

for s in "${OBFUSCATE[@]}"
do
    f="${s%%&&&*}"
    t="${s##*&&&}"
    oSTR="${oSTR}s/$f/$t/g;"
done

echo $oSTR
sed -r -iSTR -e "$oSTR" "$CODIR/$TYPE/"*.txt



echo "###################################################"
echo "## Do not forget obfuscate other output:         ##"
echo "##   passwords, secrets, keys, certificates      ##"
echo "##   descriptions, names and other ...           ##"
echo "###################################################"
