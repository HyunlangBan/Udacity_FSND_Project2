import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
import math

from models import setup_db, Question, Category, db

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page-1)*QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    app = Flask(__name__)
    setup_db(app)

    cors = CORS(app, resources={r"/*": {"origins": "*"}})

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PUT,POST,DELETE,OPTIONS')
        return response

    @app.route('/categories')
    def get_cateories():
        category = Category.query.all()
        categories = {}

        for c in category:
          categories[c.id] = c.type
            
        return jsonify(
            {
                'success': True,
                'categories': categories
            }
        )

    @app.route('/questions')
    def get_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)
        category = Category.query.all()
        categories = {}

        for c in category:
          categories[c.id] = c.type
        
        if len(current_questions) == 0:
            abort(404)

        return jsonify(
            {
                'success': True,
                'questions': current_questions,
                'total_questions': len(Question.query.all()),
                "categories": categories,
                'current_category': None
            }
        )

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        question = Question.query.filter(
            Question.id == question_id).one_or_none()

        if question is None:
            abort(404)

        question.delete()
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(Question.query.all())
        })

    @app.route('/questions', methods=['POST'])
    def create_question():
        search = request.args.get('searchTerm', None, type=str)

        if search:
            selection = Question.query.order_by(Question.id).filter(
                Question.question.ilike('%{}%'.format(search)))
            current_questions = paginate_questions(request, selection)

            return jsonify(
                {
                    'success': True,
                    'questions': current_questions,
                    'total_questions': len(current_questions),
                }
            )

        else:
            body = request.get_json()

            question = body.get('question')
            answer = body.get('answer')
            category = body.get('category')
            difficulty = body.get('difficulty')

            new_question = Question(question=question, answer=answer,
                                    category=category, difficulty=difficulty)
            new_question.insert()

            question = Question.query.order_by(Question.id.desc()).first()

        return jsonify(
            {
                'success': True,
                'question': question.question,
                'answer': question.answer,
                'difficulty': question.difficulty,
                'category': question.category
            }
        )

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_by_category(category_id):
        selection = Question.query.order_by(Question.id).filter(
            Question.category == category_id).all()

        categories = {
            1: "Science",
            2: "Art",
            3: "Geography",
            4: "History",
            5: "Entertainment",
            6: "Sports"
        }

        if selection == []:
            abort(404)

        current_questions = paginate_questions(request, selection)
        current_category = categories[category_id]
        return jsonify(
            {
                'success': True,
                'current_questions': current_questions,
                'total_questions': len(current_questions),
                'current_category': current_category
            }
        )

    @app.route('/quizzes', methods=['POST'])
    def post_quizzes():
        body = request.get_json()

        category_id = body.get('category_id', None)
        previous_questions = body.get('previous_questions', None)

        if category_id is not None:
            if previous_questions is not None:
                questions = Question.query.filter(
                    Question.id.notin_(previous_questions),
                    Question.category == category_id).all()
            else:
                questions = Question.query.filter(
                    Question.category == category_id).all()

        else:
            if previous_questions is not None:
                questions = Question.query.filter(
                    Question.id.notin_(previous_questions)).all()
            else:
                questions = Question.query.all()

        max = len(questions)-1

        if max > 0:
            question = questions[random.randint(0, max)].format()
        else:
            question = False

        return jsonify({
            'success': True,
            'question': question
        })

    @app.errorhandler(404)
    def not_found(error):
        return jsonify(
            {
                'success': False,
                'message': 'resource not found',
                'error': 404
            }
        ), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify(
            {
                'success': False,
                'message': 'Method not allowed',
                'error': 405
            }
        ), 405

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            'success': False,
            'maessage': 'unprocessable',
            'error': 422
        }), 422

    return app
