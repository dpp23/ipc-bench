#!/bin/bash



CUR_DIR=$(pwd)

RESULTS_DIR=../../results
OUT_DIR=test
HTML_OUTFILE=results.html

cp ./compare.html ${OUT_DIR}/details

cd ${RESULTS_DIR}
RESULTS=$(ls tmp*.tar.gz)
cd ${CUR_DIR}

# Generate results.html
cat ${PWD}/html_head.tmpl > ${OUT_DIR}/${HTML_OUTFILE}.new
cat ${PWD}/html_results_head.tmpl >> ${OUT_DIR}/${HTML_OUTFILE}.new
for r in ${RESULTS}; do
  ARCHIVE=${r}
  echo -n "Extracting ${ARCHIVE}..."
  tar -xzf ${RESULTS_DIR}/${ARCHIVE}
  echo " done!"
  NAME=$(echo ${r} | sed 's/\.tar\.gz//g')
  DIR=tmp/${NAME}
  # Check the extracted data directory exists
  if [[ ! -d ${DIR} ]]; then
    echo "FATAL: After extraction, ${DIR} did not exist!"
  fi

  # Find the target cores used
  TARGET_CPUS=$(cat ${DIR}/logs/target_cpus)

  # Now generate the results overview page
  python gen-overview-entry.py ${DIR} ${OUT_DIR}/${HTML_OUTFILE}.new \
    ${TARGET_CPUS} ${NAME}

  # Generate details page
  mkdir -p ${OUT_DIR}/details
  mkdir -p ${DIR}/graphs
  cat ${PWD}/html_head.tmpl > ${OUT_DIR}/details/${NAME}.html
  python gen-details-page.py ${DIR} ${OUT_DIR}/details ${TARGET_CPUS} ${NAME}
  cat ${PWD}/html_foot.tmpl >> ${OUT_DIR}/details/${NAME}.html

  # Move graphs
  mkdir -p ${OUT_DIR}/graphs
  rm -rf ${OUT_DIR}/graphs/${NAME}
  mv ${DIR}/graphs ${OUT_DIR}/graphs/${NAME}
  chmod -R g+rx ${OUT_DIR}/graphs/${NAME}
  chmod -R o+rx ${OUT_DIR}/graphs/${NAME}

  #Create file with the throughput file names
  #cd ${OUT_DIR}/graphs/${NAME}
  #find .  -not -name "*small*" -name "core*" -exec basename {} \;   >> g_cores.txt
  #cd ../../..

done
cat ${PWD}/html_results_foot.tmpl >> ${OUT_DIR}/${HTML_OUTFILE}.new
cat ${PWD}/html_foot.tmpl >> ${OUT_DIR}/${HTML_OUTFILE}.new

mv ${OUT_DIR}/${HTML_OUTFILE}.new ${OUT_DIR}/${HTML_OUTFILE}
cp ./compare.html ${OUT_DIR}/details


