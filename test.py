from dateutil.rrule import rrulestr
from datetime import datetime
from schemas.event import EventOccurence

rrule_str = "FREQ=WEEKLY;BYDAY=MO;UNTIL=20250701T000000Z"
start_time = datetime.fromisoformat("2025-05-26T10:00:00Z")
end_time = datetime.fromisoformat("2025-05-26T11:00:00Z")

# rule = rrulestr(rrule_str, dtstart=start_time)

# print("Next 5 occurrences:")
# occurrences = []
# for dt in list(rule[:5]):
#     occurrences.append({
#         "start_time":str(dt),
#         "end_time":str(dt + (end_time - start_time))
#         }
#     )
# print(occurrences[0])

def expand_occurrences(count: int = 10):
        rule = rrulestr(rrule_str, dtstart=start_time)
        # Generate up to `count` occurences
        occurrences = []
        for dt in list(rule[:count]):
            occurrences.append(EventOccurence(
                start_time=dt,
                end_time=dt + (end_time - start_time)
            ))
        return occurrences

print(expand_occurrences())