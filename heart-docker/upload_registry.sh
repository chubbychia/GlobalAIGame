 #! /bin/bash
echo "Please enter your team number"
read project_name
echo "Your team number is $project_name"

docker build -t trend-hearts $(dirname "$0")/.
docker tag trend-hearts ai.registry.trendmicro.com/$project_name/trend-hearts:rank
docker tag trend-hearts ai.registry.trendmicro.com/$project_name/trend-hearts:practice

docker login ai.registry.trendmicro.com
docker push ai.registry.trendmicro.com/$project_name/trend-hearts:rank
docker push ai.registry.trendmicro.com/$project_name/trend-hearts:practice
