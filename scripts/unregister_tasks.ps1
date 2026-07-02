# Remove Aihelper scheduled tasks from this PC.
foreach ($name in "Aihelper-ExpertFeed", "Aihelper-WeeklyDigest", "Aihelper-SheetsSync") {
  Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
}
