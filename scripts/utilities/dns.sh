#
#=========================================================================================
# DNS Utilities
#

function dns_ip () {
  if [ -f "${__zimagi_binary_dir}/kubectl" ]; then
    echo "$(${__zimagi_binary_dir}/kubectl get service nginx-nginx-ingress-controller -n nginx -o jsonpath='{.status.loadBalancer.ingress[*].ip}' 2>/dev/null)"
  fi
}

function dns_hosts () {
  if [ -f "${__zimagi_binary_dir}/kubectl" ]; then
    echo "$(${__zimagi_binary_dir}/kubectl get ingress -A -o jsonpath='{.items[*].spec.rules[*].host}' 2>/dev/null)"
  fi
}

function dns_records () {
  dns_map=("###! $ZIMAGI_APP_NAME DNS MAP !###")

  for host in $(dns_hosts); do
    for ip in $(dns_ip); do
      dns_map=("${dns_map[@]}" "$ip $host")
    done
  done

  dns_map=("${dns_map[@]}" "###! END $ZIMAGI_APP_NAME DNS MAP !###")
  dns_map="$(printf "%s\n" "${dns_map[@]}")"
  echo "$dns_map"
}

function remove_dns_records () {
  if [ -f "${HOSTS_FILE:-}" ]; then
    info "Removing existing DNS records"
    sudo perl -i -p0e "s/\n\#\#\#\!\s${ZIMAGI_APP_NAME}\sDNS\sMAP\s\!\#\#\#.+\#\#\#\!\sEND\s${ZIMAGI_APP_NAME}\sDNS\sMAP\s\!\#\#\#//se" $HOSTS_FILE
  fi
}

function save_dns_records () {
  if [ -f "${HOSTS_FILE:-}" ]; then
    remove_dns_records

    dns_records="$(dns_records)"
    info "Saving DNS records:"
    info "$dns_records"
    printf "\n$dns_records" | sudo tee -a $HOSTS_FILE >/dev/null 2>&1
  fi
}
