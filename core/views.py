from django.shortcuts import render


def home_view(request):
    context = {
        'burnout_index': 67,
        'tasks': [
            {'title': 'Complete Linear Algebra',
                'priority': 'high', 'difficulty': '4/5'},
            {'title': 'Study for Midterm Exam',
                'priority': 'high', 'difficulty': '5/5'},
            {'title': 'Review Calculus Notes',
                'priority': 'medium', 'difficulty': '3/5'},
        ],
        'mood': '● ● ● ● ○',
        'energy': '● ● ● ○ ○',
    }
    return render(request, 'home.html', context)
