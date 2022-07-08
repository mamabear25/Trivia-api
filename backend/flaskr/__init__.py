from curses import flash
import sys
import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
import re

from models import setup_db, Question, Category

db = SQLAlchemy()

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    '''
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample
    route after completing the TODOs
    '''
    CORS(app, resources={'/': {'origins': '*'}})

    '''
    @TODO: Use the after_request decorator to set Access-Control-Allow
    '''

    #  done
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorization, true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET, POST, PATCH, DELETE, OPTIONS')

        return response
    '''
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    '''

    #  done
    #  this decorator handles GET requests for all
    #  categories available in the db
    @app.route('/categories')
    def get_categories():
        #  This query returns all available categories
        categories = Category.query.all()
        #  empty dictionary holds all returned categories
        returned_categories = {}
        for category in categories:
            returned_categories[category.id] = category.type

        if (len(returned_categories) == 0):
            abort(404)

        return jsonify({
            'success': True,
            'categories': returned_categories
        })

        '''
        @TODO:
        Create an endpoint to handle GET requests for questions,
        including pagination (every 10 questions).
        This endpoint should return a list of questions,
        number of total questions, current category, categories.

        TEST: At this point, when you start the application
        you should see questions and categories generated,
        ten questions per page and pagination at the bottom of the screen
        for three pages.
        Clicking on the page numbers should update the questions.
        '''

    #  done
    #  this decorator handles GET requests for all categories
    # available in the db
    @app.route('/questions')
    def get_questions():
        #  This query returns all questions
        selection = Question.query.all()
        # returns total number of questions
        total_questions = len(selection)
        # returns paginated questions
        current_questions = paginate_questions(request, selection)

        if len(current_questions) == 0:
            abort(404)

        try:
            # this query gets all categories
            categories = Category.query.all()
            # empty dictionary holds all returned categories
            returned_categories = {}
            for category in categories:
                returned_categories[category.id] = category.type

            return jsonify({
              'success': True,
              'questions': current_questions,
              'total_questions': total_questions,
              'categories': returned_categories
            })

        except Exception:
            db.session.rollback()
            flash(sys.exc_info())
            abort(422)
        finally:
            db.session.close()

    '''
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question,
    the question will be removed.
    This removal will persist in the database and when you refresh the page.
    '''

    #  done
    # question is deleted by question_id
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.get(question_id)
            question.delete()

            return jsonify({
              'success': True,
              'deleted': question_id
            })
        except Exception:
            abort(422)

    '''
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at
    the end of the last page
    of the questions list in the "List" tab.
    '''
    #  done
    @app.route('/questions', methods=['POST'])
    def add_question():
        body = request.get_json()
        #  if new data not entered or entered incorrectly... abort
        if not ('question' in body and 'answer' in body and
                'difficulty' in body and 'category' in body):
            abort(422)
            #  thius gets data to successfully add a new question
        new_question = body.get('question')
        new_answer = body.get('answer')
        new_difficulty = body.get('difficulty')
        new_category = body.get('category')

        try:
            question = Question(question=new_question,
                                answer=new_answer,
                                difficulty=new_difficulty,
                                category=new_category)
            question.insert()

            return jsonify({
              'success': True,
              'created': question.id,
            })
        except Exception:
            abort(422)

    '''
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    '''
    #  done
    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        search_term = request.get_json()['searchTerm']
        #  this gets the questions based on a search term using ilike will
        # return questions that has the string included in them
        question_search = Question.query.filter(Question.question.ilike
                                                (f'%{search_term}%'))
        returned_questions = [question.format() for question in
                              question_search]
        # returns the number of questions searched for using
        # partial string method
        total_count = question_search.count()

        response = {
          'total_questions': total_count,
          'questions': returned_questions,
          'success': True
        }
        print(response)

        return jsonify(response)

    '''
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    '''
    #  done
    # get questions by category
    @app.route('/categories/<int:id>/questions')
    def get_questions_by_category(id):
        #  gets question by the id
        category = Category.query.filter_by(id=id).one_or_none()

        if (category) == 0:
            abort(400)
        #  gets all questions in a category
        categories = Question.query.filter_by(category=str(category.id)).all()
        # returns paginated queustions based on category(10/page)
        paginated_questions = paginate_questions(request, categories)

        return jsonify({
          'success': True,
          'questions': paginated_questions,
          'total_questions': len(Question.query.all()),
          'current_category': category.type
        })

    '''
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    '''

    #  done
    @app.route('/quizzes', methods=['POST'])
    def get_quiz():
        try:
            body = request.get_json()
            category = body.get('quiz_category')
            previous_questions = body.get('previous_questions')

            if category['type'] == 'click':
                returned_questions = Question.query.filter(
                        Question.id.notin_((previous_questions))).all()

            else:
                returned_questions = Question.query.filter_by(
                  category=category['id']).filter(
                    Question.id.notin_((previous_questions))).all()

            new_question = returned_questions[random.randrange(
                  0, len(returned_questions))].format() if len(
              returned_questions) > 0 else None

            return jsonify({
              'success': True,
              'question': new_question
            })
        except Exception:
            abort(422)

    #  done
    '''
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    '''
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
          "success": False,
          "error": 404,
          "message": "Resource Not Found"
        }), 404

    @app.errorhandler(422)
    def UnProcessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "UnProcessable"
          }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
          "success": False,
          "error": 400,
          "message": "Bad Request"
        }), 400

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
          "success": False,
          "error": 500,
          "message": "Internal Server Error... Try again!"
        }), 500

    return app
