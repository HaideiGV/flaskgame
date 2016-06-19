from flask.ext.login import LoginManager
from flask_wtf.csrf import CsrfProtect

login_manager = LoginManager()
csrf = CsrfProtect()


def get_all_combos(arr):
	result = []
	for i in range(len(arr)-1):
		j = i+1
		for j in range(j, len(arr)):
			k = j+1
			for k in range(k, len(arr)):
				temp = []
				temp.append(arr[i])
				temp.append(arr[j])
				temp.append(arr[k])
				if temp in result:
					pass
				else:
					result.append(sorted(temp))
	return result