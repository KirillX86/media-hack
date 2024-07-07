from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uuid
import os
from catboost import CatBoostRegressor
from scipy.optimize import differential_evolution, LinearConstraint, NonlinearConstraint
# import cvxpy as cp
import pandas as pd
import numpy as np
# from datetime import datetime

MAX_BILLBOARD_COUNT = 14000
MAX_CAMPAIGN_BUDGET = 1e12
MIN_AGE = 12
MAX_AGE = 100
COSTS = [1]*25




app = FastAPI()

# Настройка CORS
origins = [
    "http://localhost",
    "http://localhost:5500",
    "http://127.0.0.1",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Пример данных: список районов и их трехбуквенные идентификаторы на латинице
moscow_districts = [
    {"name": "Akademichesky", "id": "AKD"},
    {"name": "Alekseevsky", "id": "ALK"},
    {"name": "Altufyevsky", "id": "ALT"},
    {"name": "Arbat", "id": "ARB"},
    {"name": "Aeroport", "id": "AER"},
    {"name": "Babushkinsky", "id": "BAB"},
    {"name": "Basmanny", "id": "BSM"},
    {"name": "Begovoy", "id": "BEG"},
    {"name": "Beskudnikovsky", "id": "BES"},
    {"name": "Bibirevo", "id": "BIB"},
    {"name": "Biryulevo Vostochnoye", "id": "BIV"},
    {"name": "Biryulevo Zapadnoye", "id": "BIZ"},
    {"name": "Bogorodskoye", "id": "BGR"},
    {"name": "Brateyevo", "id": "BRT"},
    {"name": "Butyrsky", "id": "BUT"},
    {"name": "Veshnyaki", "id": "VES"},
    {"name": "Vnukovo", "id": "VNU"},
    {"name": "Voykovsky", "id": "VOY"},
    {"name": "Voskresenskoye", "id": "VSK"},
    {"name": "Vykhino-Zhulebino", "id": "VZH"},
    {"name": "Gagarinsky", "id": "GAG"},
    {"name": "Golovinsky", "id": "GLV"},
    {"name": "Golyanovo", "id": "GLY"},
    {"name": "Danilovsky", "id": "DAN"},
    {"name": "Degunino Vostochnoye", "id": "DGV"},
    {"name": "Degunino Zapadnoye", "id": "DGZ"},
    {"name": "Dmitrovsky", "id": "DMT"},
    {"name": "Donskoy", "id": "DON"},
    {"name": "Dorogomilovo", "id": "DOR"},
    {"name": "Zamoskvorechye", "id": "ZMS"},
    {"name": "Zapadnoye Degunino", "id": "ZDG"},
    {"name": "Zyuzino", "id": "ZUZ"},
    {"name": "Zyablikovo", "id": "ZBL"},
    {"name": "Ivanovskoye", "id": "IVN"},
    {"name": "Izmaylovo Vostochnoye", "id": "IVE"},
    {"name": "Izmaylovo Severnoye", "id": "IVS"},
    {"name": "Izmaylovo", "id": "IZM"},
    {"name": "Kapotnya", "id": "KPT"},
    {"name": "Konkovo", "id": "KNK"},
    {"name": "Koptevo", "id": "KOP"},
    {"name": "Kosino-Ukhtomsky", "id": "KSU"},
    {"name": "Kotlovka", "id": "KTL"},
    {"name": "Krasnoselsky", "id": "KRS"},
    {"name": "Krylatskoye", "id": "KRL"},
    {"name": "Kuzminki", "id": "KZM"},
    {"name": "Kuntsevo", "id": "KNC"},
    {"name": "Kurkino", "id": "KUR"},
    {"name": "Levoberezhny", "id": "LVB"},
    {"name": "Lianozovo", "id": "LNZ"},
    {"name": "Lomonosovsky", "id": "LMN"},
    {"name": "Losinoostrovsky", "id": "LSO"},
    {"name": "Lyublino", "id": "LUB"},
    {"name": "Marfino", "id": "MAR"},
    {"name": "Maryina Roshcha", "id": "MRR"},
    {"name": "Maryino", "id": "MRN"},
    {"name": "Matushkino", "id": "MTK"},
    {"name": "Metrogorodok", "id": "MTG"},
    {"name": "Meshchansky", "id": "MSH"},
    {"name": "Mitino", "id": "MTN"},
    {"name": "Mozhaysky", "id": "MOZ"},
    {"name": "Molzhaninovsky", "id": "MLZ"},
    {"name": "Moskvorechye-Saburovo", "id": "MSK"},
    {"name": "Nagatino-Sadovniki", "id": "NGS"},
    {"name": "Nagatinsky Zaton", "id": "NGZ"},
    {"name": "Nagorny", "id": "NGR"},
    {"name": "Nekrasovka", "id": "NKR"},
    {"name": "Novogireyevo", "id": "NVG"},
    {"name": "Novokosino", "id": "NKS"},
    {"name": "Novoperedelkino", "id": "NPD"},
    {"name": "Novoslobodsky", "id": "NSB"},
    {"name": "Obruchevsky", "id": "OBR"},
    {"name": "Orekhovo-Borisovo Severnoye", "id": "OBS"},
    {"name": "Orekhovo-Borisovo Yuzhnoye", "id": "OBY"},
    {"name": "Ostankinsky", "id": "OST"},
    {"name": "Otradnoye", "id": "OTR"},
    {"name": "Ochakovo-Matveyevskoye", "id": "OCM"},
    {"name": "Perovo", "id": "PRV"},
    {"name": "Pechatniki", "id": "PCH"},
    {"name": "Pokrovskoye-Streshnevo", "id": "PKS"},
    {"name": "Preobrazhenskoye", "id": "PRB"},
    {"name": "Presnensky", "id": "PRS"},
    {"name": "Prospekt Vernadskogo", "id": "PVN"},
    {"name": "Ramenki", "id": "RMK"},
    {"name": "Rostokino", "id": "RST"},
    {"name": "Ryazansky", "id": "RZN"},
    {"name": "Savyolovsky", "id": "SVL"},
    {"name": "Sviblovo", "id": "SVB"},
    {"name": "Silino", "id": "SLN"},
    {"name": "Severnoye Butovo", "id": "SBT"},
    {"name": "Severnoye Izmaylovo", "id": "SIZ"},
    {"name": "Severnoye Medvedkovo", "id": "SMD"},
    {"name": "Severny", "id": "SVR"},
    {"name": "Sokol", "id": "SKL"},
    {"name": "Sokolniki", "id": "SKN"},
    {"name": "Solntsevo", "id": "SLN"},
    {"name": "Strogino", "id": "STR"},
    {"name": "Tagansky", "id": "TGN"},
    {"name": "Tverskoy", "id": "TVR"},
    {"name": "Tekstilshchiki", "id": "TKS"},
    {"name": "Teply Stan", "id": "TPL"},
    {"name": "Timiryazevsky", "id": "TMR"},
    {"name": "Troparevo-Nikulino", "id": "TRN"},
    {"name": "Tushino Severnoye", "id": "TSN"},
    {"name": "Tushino Yuzhnoye", "id": "TYN"},
    {"name": "Filyovsky Park", "id": "FLP"},
    {"name": "Fili-Davydkovo", "id": "FLD"},
    {"name": "Khamovniki", "id": "HMN"},
    {"name": "Khoroshyovo-Mnyovniki", "id": "HRM"},
    {"name": "Khoroshyovsky", "id": "HRH"},
    {"name": "Tsaritsyno", "id": "CRC"},
    {"name": "Cheryomushki", "id": "CHM"},
    {"name": "Chertanovo Severnoye", "id": "CHS"},
    {"name": "Chertanovo Tsentralnoye", "id": "CHC"},
    {"name": "Chertanovo Yuzhnoye", "id": "CHY"},
    {"name": "Shchukino", "id": "SHK"},
    {"name": "Yuzhnoye Butovo", "id": "YBT"},
    {"name": "Yuzhnoye Medvedkovo", "id": "YMD"},
    {"name": "Yakimanka", "id": "YKM"},
    {"name": "Yaroslavsky", "id": "YRS"},
    {"name": "Yasenevo", "id": "YSN"}
]

@app.get("/districts")
def get_districts():
    return moscow_districts

# Запуск приложения (обычно это делается в отдельном файле при помощи uvicorn)
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)

# Пример данных: список административных округов и их уникальные идентификаторы
moscow_administrative_districts = [
    {"name": "ЦАО", "id": "CAD"},
    {"name": "САО", "id": "SAD"},
    {"name": "СВАО", "id": "SVAD"},
    {"name": "ВАО", "id": "EAD"},
    {"name": "ЮВАО", "id": "SEAD"},
    {"name": "ЮАО", "id": "SAD"},
    {"name": "ЮЗАО", "id": "SWAD"},
    {"name": "ЗАО", "id": "WAD"},
    {"name": "СЗАО", "id": "NWAD"}
]

@app.get("/administrative_districts")
def get_administrative_districts():
    return moscow_administrative_districts

# Запуск приложения (обычно это делается в отдельном файле при помощи uvicorn)
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)


# # Директория для сохранения загруженных файлов
# UPLOAD_DIRECTORY = "./uploads"

# # Создание директории, если она не существует
# if not os.path.exists(UPLOAD_DIRECTORY):
    # os.makedirs(UPLOAD_DIRECTORY)

@app.post("/load_prices")
async def load_prices(file: UploadFile = File(...)):
    # # Проверка допустимых форматов файлов
    # if file.content_type not in ["application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "text/csv"]:
        # raise HTTPException(status_code=400, detail="Unsupported file type.")
    
    # # Генерация уникального идентификатора для файла
    file_id = str(uuid.uuid4())
    # file_extension = os.path.splitext(file.filename)[1]
    # file_path = os.path.join(UPLOAD_DIRECTORY, f"{file_id}{file_extension}")

    # # Сохранение файла
    # with open(file_path, "wb") as buffer:
        # buffer.write(await file.read())
    
    return {"file_id": file_id}

def optimize_within_cluster(cluster_id, bilboard_count, dists, unique_points):

    # # Пример входных данных
    # unique_points = pd.DataFrame({'id': [0, 1, 2, 3, 4]})
    # dists = pd.DataFrame({
    #     'b1': [0, 0, 0, 0, 1, 1, 1, 2, 2, 3],
    #     'b2': [1, 2, 3, 4, 2, 3, 4, 3, 4, 4],
    #     'dist': [2, 3, 4, 5, 4, 1, 2, 2, 3, 4]
    # })

    # {6.0, 7.0, 8.0, 11.0, 12.0, 13.0, 16.0, 17.0, 18.0}
    N = bilboard_count
    if len(unique_points) == 0 or bilboard_count == 0:
        return []
    unique_points_df = unique_points
    unique_points = unique_points.loc[unique_points["cluster_id"].eq(cluster_id)]
    dst = dists.loc[dists["b1"].isin(unique_points["id"]) & dists["b2"].isin(unique_points["id"])]
    dst = {(row["b1"], row["b2"]): row["dist"] for idx, row in dists.iterrows()}
    
    unique_points = [row.to_dict() for idx, row in unique_points.iterrows()]

    # Инициализация: выбираем произвольную точку, например, точку с id = unique_points[0]['id']
    selected_points = [unique_points[0]['id']]
    num_points = len(unique_points)

    while len(selected_points) < N:
        max_min_distance = -1
        next_point = -1

        for point in unique_points:
            if point['id'] in selected_points:
                continue

            # Находим минимальное расстояние до уже выбранных точек
            d = [dst[(point['id'], selected_point)] if (point['id'], selected_point) in dst
                 else 1000 for selected_point in selected_points]
            
            min_distance = min(d)

            # Выбираем точку, которая максимизирует минимальное расстояние
            if min_distance > max_min_distance:
                max_min_distance = min_distance
                next_point = point['id']

        selected_points.append(next_point)
        
    selected_points = [row.to_dict() for idx, row in unique_points_df.loc[unique_points_df["id"].isin(selected_points)].iterrows()]

    return selected_points

# # dists = pd.read_excel("./unique_points_cluster_25_distances_le1000.xlsx")
# # unique_points = pd.read_excel("./unique_points_cluster_25.xlsx")
# N = 25
# print(datetime.now())
# selected_points = optimize_within_cluster(6, N, dists, unique_points)
# print(datetime.now())
# print("Выбранные точки:", selected_points)

@app.post("/optimize")
async def optimize(
    file_id: str,
    gender: str,
    age_from: int,
    age_to: int,
    income_a: bool,
    income_b: bool,
    income_c: bool,
    campaign_budget: Optional[int] = Query(default=-1),
    billboard_count: Optional[int] = Query(default=-1),
    districts: List[str] = Query(...),
    areas: List[str] = Query(...)
):
    male = 1 if gender in ("male", "all") else 0
    female = 1 if gender in ("female", "all") else 0
    income_a = 1 if income_a else 0
    income_b = 1 if income_b else 0
    income_c = 1 if income_c else 0
    campaign_budget = campaign_budget \
            if campaign_budget != -1 and type(campaign_budget) != type(Query()) \
                else MAX_CAMPAIGN_BUDGET
    billboard_count = billboard_count \
            if billboard_count != -1 and type(billboard_count) != type(Query()) \
                else MAX_BILLBOARD_COUNT
        
    # # Проверка существования файла
    # file_path = os.path.join(UPLOAD_DIRECTORY, f"{file_id}.csv")
    # if not os.path.exists(file_path):
        # file_path = os.path.join(UPLOAD_DIRECTORY, f"{file_id}.xlsx")
        # if not os.path.exists(file_path):
            # raise HTTPException(status_code=404, detail="File not found.")

    # # Имитация процесса оптимизации (на основе переданных параметров)
    # # Загрузите файл и выполните необходимые расчеты

    dists = pd.read_excel("data/unique_points_cluster_25_distances_le1000.xlsx")
    unique_points = pd.read_excel("data/unique_points_cluster_25.xlsx")
    model_ = CatBoostRegressor()
    model_.load_model('data/catboost_model_1.cbm')
    
    # Определение границ для каждого параметра
    bounds = [
        (MIN_AGE, age_from),  # ageFrom
        (age_to, MAX_AGE),  # ageTo
        (0, 15),    # distance_msc_centre_mean
        (0, 15),    # distance_msc_centre_median
        (0, 15),    # distance_msc_centre_std
        (0, 15),    # distance_msc_centre_mean_trim
        *( [(0, billboard_count)] * 25 ),  # cluster_0 - cluster_24
        (income_a, 1),     # salary_a
        (income_b, 1),     # salary_b
        (income_c, 1),     # salary_c
        (male, 1),     # male
        (female, 1),     # female
        (0, billboard_count)   # num_points
    ]
    
    bb_len = {c: len(unique_points.loc[unique_points["cluster_id"].eq(i)]) for i, c in enumerate(range(6, 31))}
    
    for k, v in bb_len.items():
        bounds[k] = (bounds[k][0], min(billboard_count, v))

    # Определение максимальной суммы переменных (если требуется)
    max_sum = 150  # Замените на ваше значение, если необходимо

    # Функция штрафа за нарушение ограничения
    def penalty(x):
        penalty_value = 0
        # добавьте штрафы за другие ограничения, если необходимо
        return penalty_value

    # Функция, которую мы будем оптимизировать
    def objective_function(x):
        x = np.round(x).astype(int)  # преобразование к целым числам
        penalty_value = penalty(x)
        return -model_.predict(np.array([x]))[0] + penalty_value  # знак минус для максимизации и добавление штрафа

    # Линейное ограничение: сумма всех элементов x[6:31] должна быть не более 20
    A = np.zeros(len(bounds))
    A[6:31] = 1  # коэффициенты линейного ограничения для x[6:31]
    lb = -np.inf  # нижняя граница неограничена
    ub = billboard_count  # верхняя граница равна 20
    linear_constraint = LinearConstraint(A, lb, ub)
    # Второе линейное ограничение: произведение исходного вектора на вектор cost не более чем campaign_budget
    A_cost = np.zeros(len(bounds)) # коэффициенты линейного ограничения для стоимости
    A_cost[6:31] = COSTS
    lb_cost = -np.inf  # нижняя граница неограничена
    ub_cost = campaign_budget  # верхняя граница равна campaign_budget
    linear_constraint_cost = LinearConstraint(A_cost, lb_cost, ub_cost)    # Выполнение дифференциальной эволюции с линейными ограничениями
    constraints = [linear_constraint, linear_constraint_cost]    

    # Выполнение дифференциальной эволюции
    result = differential_evolution(objective_function, bounds, 
                                    constraints=(linear_constraint,), 
                                    strategy='best1bin', 
                                    maxiter=1000, popsize=15, tol=0.01, mutation=(0.5, 1), 
                                    recombination=0.7, seed=42, callback=None, 
#                                     disp=True, 
                                    polish=True, init='latinhypercube', 
                                    atol=0, updating='deferred', workers=1)
    
    # Преобразование оптимальных значений в целые числа
    optimal_args = np.round(result.x).astype(int)
    max_value = -result.fun  # верните знак обратно для получения максимального значения
    
    oc = optimal_args[6:31]
    
#     print(f'Оптимальные аргументы: {optimal_args[6:31], sum(optimal_args[6:31])}')
#     print(f'Максимальное значение: {max_value}')
    
    points = []

    for i, c in enumerate(oc):
        points = points + optimize_within_cluster(i, c, dists, unique_points)        

    print(points)

    return {"points": points}

@app.get("/optimize_test")
async def optimize_test():
    return await optimize("", "all", 12, 100, True, True, True, campaign_budget = 50, billboard_count = 50)

# Запуск приложения (обычно это делается в отдельном файле при помощи uvicorn)
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
