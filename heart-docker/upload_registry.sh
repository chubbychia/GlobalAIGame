 #! /bin/bash
echo "Please enter your team number"
read project_name
echo "Your team number is $project_name"

docker build -t trend-hearts $(dirname "$0")/.
docker tag trend-hearts ai.registry.trendmicro.com/$project_name/trend-hearts:rank
docker tag trend-hearts ai.registry.trendmicro.com/$project_name/trend-hearts:practice

docker login ai.registry.trendmicro.com
rc=$?
if [[ $rc != 0 ]]; then
    echo "Please enter your AD username to login trendmicro registry"
    read username
    echo "Please enter your AD password to login trendmicro registry"
    read -s -p "Password:" pswd
    docker login -u $username -p $pswd ai.registry.trendmicro.com
fi

docker push ai.registry.trendmicro.com/$project_name/trend-hearts:rank
docker push ai.registry.trendmicro.com/$project_name/trend-hearts:practice
