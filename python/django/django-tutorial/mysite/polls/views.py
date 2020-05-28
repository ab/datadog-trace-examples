import base64
import os
from ddtrace import tracer
from ddtrace.helpers import get_correlation_ids
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone

from .models import Choice, Question


class IndexView(generic.ListView):
    template_name = 'polls/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
        """Return the last five published questions."""
        return Question.objects.filter(
                pub_date__lte=timezone.now()
            ).order_by('-pub_date')[:5]


class DetailView(generic.DetailView):
    model = Question
    template_name = 'polls/detail.html'

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())


class ResultsView(generic.DetailView):
    model = Question
    template_name = 'polls/results.html'


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(request, 'polls/detail.html', {
            'question': question,
            'error_message': "You didn't select a choice.",
        })
    else:
        selected_choice.votes += 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))


def trace_test(request, spans=1, junk=False):
    for i in range(1, spans+1):
        with tracer.trace('test span', resource=f"number {i}") as span:
            span.set_tag("index", i)
            if junk:
                span.set_tag("random junk", base64.encodebytes(os.urandom(33)))

    trace_id, span_id = get_correlation_ids()

    return HttpResponse(
        content="\n".join([
            f"OK, generated at least {spans} spans.",
            f"Trace ID: {trace_id}",
            f"Span ID: {span_id}",
            "",
        ]),
        content_type="text/plain")
