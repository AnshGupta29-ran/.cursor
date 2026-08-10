using UnityEngine;

public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }
    public Board Board;
    public PlayerController Player;
    public AIController AI;
    public ManaPool ManaPool;
    public Frostline Frostline;
    public GlacialPulse GlacialPulse;
    public float TurnTimer = 30f;
    private float _timer;
    private bool _playerTurn = true;

    void Awake()
    {
        if (Instance != null && Instance != this) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    void Start()
    {
        _timer = TurnTimer;
        // Initialize components if they are not set via inspector
        if (Board == null) Board = FindObjectOfType<Board>();
        if (Player == null) Player = FindObjectOfType<PlayerController>();
        if (AI == null) AI = FindObjectOfType<AIController>();
        if (ManaPool == null) ManaPool = FindObjectOfType<ManaPool>();
        if (Frostline == null) Frostline = FindObjectOfType<Frostline>();
        if (GlacialPulse == null) GlacialPulse = FindObjectOfType<GlacialPulse>();
        BeginTurn();
    }

    void Update()
    {
        _timer -= Time.deltaTime;
        if (_timer <= 0f)
        {
            EndTurn();
        }
    }

    public void BeginTurn()
    {
        _timer = TurnTimer;
        if (_playerTurn)
        {
            Player.StartTurn();
        }
        else
        {
            AI.StartTurn();
        }
    }

    public void EndTurn()
    {
        if (_playerTurn)
        {
            Player.EndTurn();
        }
        else
        {
            AI.EndTurn();
        }
        // Advance common mechanics
        ManaPool.GainMana(1);
        Frostline.Advance();
        GlacialPulse.UpdateDifficulty();
        _playerTurn = !_playerTurn;
        BeginTurn();
    }
}
