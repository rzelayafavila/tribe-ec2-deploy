#run on the machine you're moving from
sudo -u tribe pg_dump dbname=tribe -F c -f /var/dumps/tribedump
scp -i ~/greenelab.pem /var/dumps/tribedump  ubuntu@ec2-54-88-200-48.compute-1.amazonaws.com:/db/

#run on the machine you're moving to (assumes database exists and will be overwritten):
pg_restore -h tribe.cobepk65dd7j.us-east-1.rds.amazonaws.com -U tribe -d tribe /db/tribedump -W -e

